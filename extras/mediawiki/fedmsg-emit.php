<?php
/*
 * fedmsg-emit.php
 * -------------------------
 *
 * A MediaWiki plugin that emits messages to the Fedora Infrastructure Message
 * Bus.
 *
 * Installation Instructions
 * -------------------------
 *
 * You need to enable the following in /etc/php.ini for this to fly:
 *
 *    extension=zmq.so
 *
 * To install the plugin for mediawiki, you need to copy this file to:
 *
 *    /usr/share/mediawiki/fedmsg-emit.php
 *
 * And you also need to enable it by adding the following to the bottom of
 * /var/www/html/wiki/LocalSettings.php
 *
 *    require_once("$IP/fedmsg-emit.php");
 *
 * This corner of the fedmsg topology requires that an instance of fedmsg-relay
 * be running somewhere.  The reason being that multiple php processes get run
 * by apache at the same time which would necessitate `n` different bind
 * addresses for each process.  Here, as opposed to 'normal' fedmsg
 * configurations in our python webapps, each php process actively connects to
 * the relay and emits messages.  Our 'normal' python webapps establish a
 * passive endpoint on which they broadcast messages.
 *
 * Miscellaneous
 * -------------
 *
 * Version:   0.2.0
 * License:   LGPLv2+
 * Author:    Ralph Bean
 * Source:    http://github.com/ralphbean/fedmsg
 */

if (!defined('MEDIAWIKI')) {echo("Cannot be run outside MediaWiki"); die(1);}

$wgHooks['ArticleSaveComplete'][] = 'article_save';
$wgHooks['UploadComplete'][] = 'upload_complete';

// globals
$config = 0;
$queue = 0;

// A utility function, taken from the comments at
// http://php.net/manual/en/language.types.boolean.php
function to_bool ($_val) {
  $_trueValues = array('yes', 'y', 'true');
  $_forceLowercase = true;

  if (is_string($_val)) {
    return (in_array(
      ($_forceLowercase?strtolower($_val):$_val),
      $_trueValues
    ));
  } else {
    return (boolean) $_val;
  }
}


function initialize() {
  global $config, $queue;
  /* Load the config.  Create a publishing socket. */

  // Danger! Danger!
  $json = shell_exec("fedmsg-config");
  $config = json_decode($json, true);

  /* Just make sure everything is sane with the fedmsg config */
  if (!array_key_exists('relay_inbound', $config)) {
    echo("fedmsg-config has no 'relay_inbound'");
    die(1);
  }

  $context = new ZMQContext(1, true);
  $queue = $context->getSocket(ZMQ::SOCKET_PUB, "pub-a-dub-dub");
  $queue->connect($config['relay_inbound']);
}

initialize();


# This is a reimplementation of the python code in fedmsg/crypto.py
# That file is authoritative.  Changes there should be reflected here.
function sign_message($message_obj) {
  global $config;

  $message = json_encode($message_obj);

  # Step 0) - Find our cert.
  $fqdn = gethostname();
  $tokens = explode('.', $fqdn);
  $hostname = $tokens[0];
  $ssldir = $config['ssldir'];
  $certname = $config['certnames']['mediawiki.'.$hostname];

  # Step 1) - Load and encode the X509 cert
  $cert_obj = openssl_x509_read(file_get_contents(
    $ssldir.'/certs/'.$certname.".pem"
  ));
  $cert = "";
  openssl_x509_export($cert_obj, $cert);
  $cert = base64_encode($cert);

  # Step 2) - Load and sign the jsonified message with the RSA private key
  $rsa_private = openssl_get_privatekey(file_get_contents(
    $ssldir.'/private_keys/'.$certname.".pem"
  ));
  $signature = "";
  openssl_sign($message, $signature, $rsa_private);
  $signature = base64_encode($signature);

  # Step 3) - Stuff it back in the message and return
  $message_obj['signature'] = $signature;
  $message_obj['certificate'] = $cert;

  return $message_obj;
}


function emit_message($subtopic, $message) {
  global $config, $queue;

  # Re-implement some of the logc from fedmsg/core.py
  # We'll have to be careful to keep this up to date.
  $prefix = "org.fedoraproject." . $config['environment'] . ".wiki.";
  $topic = $prefix . $subtopic;

  $message_obj = array(
    "topic" => $topic,
    "msg" => $message,
    "timestamp" => time(),
  );
  if (array_key_exists('sign_messages', $config) and to_bool($config['sign_messages'])) {
    $message_obj = sign_message($message_obj);
  }

  $envelope = json_encode($message_obj);
  $queue->send($topic, ZMQ::MODE_SNDMORE);
  $queue->send($envelope);
}

function article_save(
  &$article,
  &$user,
  $text,
  $summary,
  $minoredit,
  $watchthis,
  $sectionanchor,
  &$flags,
  $revision,
  &$status,
  $baseRevId
) {

  $topic = "article.edit";
  $title = $article->getTitle();
  if ( $title->getNsText() ) {
    $titletext = $title->getNsText() . ":" . $title->getText();
  } else {
    $titletext = $title->getText();
  }

  # Just send on all the information we can...  change the attr names to be
  # more pythonic in style, though.
  $msg = array(
    "title" => $titletext,
    "user" => $user->getName(),
    "text" => $text,
    "summary" => $summary,
    "minor_edit" => $minoredit,
    "watch_this" => $watchthis,
    "section_anchor" => $sectionanchor,
    "revision" => $revision,
    "base_rev_id" => $baseRevId,
    # TODO - flags?
    # TODO - status?
  );

  emit_message($topic, $msg);
  return true;
}

function upload_complete(&$image) {
  $topic = "upload.complete";
  $msg = array(
    "file_exists" => $image->getLocalFile()->fileExists,  // 1 or 0
    "media_type" => $image->getLocalFile()->media_type,   // examples: "AUDIO", "VIDEO", ...
    "mime" => $image->getLocalFile()->mime,               // example: audio/mp3
    "major_mime" => $image->getLocalFile()->major_mime,   // e.g. audio
    "minor_mime" => $image->getLocalFile()->minor_mime,   // e.g. mp3
    "size" => $image->getLocalFile()->size,               //in bytes, e.g. 2412586
    "user_id" => $image->getLocalFile()->user,            // int userId
    "user_text" => $image->getLocalFile()->user_text,     // the username
    "description" => $image->getLocalFile()->description,
    "url" => $image->getLocalFile()->url,                 // gives the relavive url for direct access of the uploaded media
    "title" => $image->getLocalFile()->getTitle(),        // gives a title object for the current media
  );

  emit_message($topic, $msg);
  return true;
}

?>
