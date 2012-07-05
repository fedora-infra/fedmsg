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

function emit_message($subtopic, $message) {
  global $config, $queue;

  # Re-implement some of the logc from fedmsg/core.py
  # We'll have to be careful to keep this up to date.
  $prefix = "org.fedoraproject." . $config['environment'] . ".wiki.";
  $topic = $prefix . $subtopic;

  $envelope = json_encode(array(
    "topic" => $topic,
    "msg" => $message,
    "timestamp" => time(),
  ));

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
