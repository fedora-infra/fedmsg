<?php
/*
 * fedmsg-emit.php
 * -------------------------
 *
 * A MediaWiki plugin that emits messages to the Federated Message Bus.
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

// A utility function to recursively sort an associative
// array by key.  Kind of like ordereddict from Python.
// Used for encoding and signing messages.
function deep_ksort(&$arr) {
    ksort($arr);
    foreach ($arr as &$a) {
        if (is_array($a) && !empty($a)) {
            deep_ksort($a);
        }
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
    return false;
  }

  $context = new ZMQContext(1, true);
  $queue = $context->getSocket(ZMQ::SOCKET_PUB, "pub-a-dub-dub");
  $queue->setSockOpt(ZMQ::SOCKOPT_LINGER, $config['zmq_linger']);

  if (is_array($config['relay_inbound'])) {
    // API for fedmsg >= 0.5.2
    // TODO - be more robust here and if connecting to the first one fails, try
    // the next, and the next, and etc...
    $queue->connect($config['relay_inbound'][0]);
  } else {
    // API for fedmsg <= 0.5.1
    $queue->connect($config['relay_inbound']);
  }

  # Go to sleep for a brief moment.. just long enough to let our zmq socket
  # initialize.
  if (array_key_exists('post_init_sleep', $config)) {
    usleep($config['post_init_sleep'] * 1000000);
  }

  return true;
}

# Register our hooks with mediawiki
$wgHooks['ArticleSaveComplete'][] = 'article_save';
$wgHooks['UploadComplete'][] = 'upload_complete';

# This is a reimplementation of the python code in fedmsg/crypto.py
# That file is authoritative.  Changes there should be reflected here.
function sign_message($message_obj) {
  global $config;

  # This is required so that the string we sign is identical in python and in
  # php.  Ordereddict is used there; ksort here.
  deep_ksort($message_obj);

  # It would be best to pass JSON_UNESCAPE_SLASHES as an option here, but it is
  # not available until php-5.4
  $message = json_encode($message_obj);
  # In the meantime, we'll remove escaped slashes ourselves.  This is
  # necessary in order to produce the exact same encoding as python (so that our
  # signatures match for validation).
  $message = stripcslashes($message);

  # Step 0) - Find our cert.
  $fqdn = gethostname();
  $tokens = explode('.', $fqdn);
  $hostname = $tokens[0];
  $ssldir = $config['ssldir'];
  $certname = $config['certnames']['mediawiki.'.$hostname];

  # Step 1) - Load and encode the X509 cert
  $cert_obj = openssl_x509_read(file_get_contents(
    $ssldir.'/'.$certname.".crt"
  ));
  $cert = "";
  openssl_x509_export($cert_obj, $cert);
  $cert = base64_encode($cert);

  # Step 2) - Load and sign the jsonified message with the RSA private key
  $rsa_private = openssl_get_privatekey(file_get_contents(
    $ssldir.'/'.$certname.".key"
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
    "timestamp" => round(time(), 3),
    "msg_id" => date("Y") . "-" . uuid_create(),
    "username" => "apache",
    # TODO -> we don't have a good way to increment this counter from php yet.
    "i" => 1,
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

  # If for some reason or another we can't create our socket, then bail.
  if (!initialize()) { return false; }

  $topic = "article.edit";
  $title = $article->getTitle();
  if ( $title->getNsText() ) {
    $titletext = $title->getNsText() . ":" . $title->getText();
  } else {
    $titletext = $title->getText();
  }

  if ( is_object($revision) ) {
    $url = $title->getFullURL('diff=prev&oldid=' . $revision->getId());
  } else {
    $url = $title->getFullURL();
  }

  # Just send on all the information we can...  change the attr names to be
  # more pythonic in style, though.
  $msg = array(
    "title" => $titletext,
    "user" => $user->getName(),
    "minor_edit" => $minoredit,
    "watch_this" => $watchthis,
    "section_anchor" => $sectionanchor,
    "revision" => $revision,
    "base_rev_id" => $baseRevId,
    "url" => $url,
    #"summary" => $summary,  # We *used* to send this, but it mucked things up.
    # https://fedorahosted.org/fedora-infrastructure/ticket/3738#comment:7
    #"text" => $text,  # We *could* send this, but it's a lot of spam.
    # TODO - flags?
    # TODO - status?
  );

  emit_message($topic, $msg);
  return true;
}

function upload_complete(&$image) {

  # If for some reason or another we can't create our socket, then bail.
  if (!initialize()) { return false; }

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
