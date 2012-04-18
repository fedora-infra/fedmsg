<?php
/*
 * fedmsg-mediawiki-emit.php
 *
 * A MediaWiki plugin that emits messages to the Fedora Infrastructure Message 
 * Bus.
 *
 * Version:   0.2.0
 * License:   LGPLv2+
 * Author:    Ralph Bean
 * Source:    http://github.com/ralphbean/fedmsg
 */ 

if (!defined('MEDIAWIKI')) {echo("Cannot be run outside MediaWiki"); die(1);}

$wgHooks['ArticleSaveComplete'][] = 'article_save';

// globals
$config = 0;
$queue = 0;

function initialize() {
  global $config, $queue;
  /* Load the config.  Create a publishing socket. */

  // Danger! Danger!
  // TODO - change this to just shell_exec("fedmsg-config")
  $json = shell_exec("fedmsg-logger --print-config");
  $config = json_decode($json, true);
  validate_config($config);

  $context = new ZMQContext();
  $queue = new ZMQSocket($context, ZMQ::SOCKET_PUB, "pub-a-dub-dub");
  $queue->bind($config['endpoints']['mediawiki']);
}

function validate_config(&$config) {
  /* Just make sure everything is sane with the fedmsg config */
  if (!array_key_exists('endpoints', $config)) {
    echo("fedmsg-config has no 'endpoints'");
    die(1);
  }
  if (!array_key_exists('mediawiki', $config['endpoints'])) {
    echo("fedmsg-config['endpoints'] has no 'mediawiki'");
    die(1);
  }
}

initialize();

function emit_message($topic, $message) {
  global $queue;
  $queue->send($topic, ZMQ::MODE_SNDMORE);
  $queue->send(json_encode($message));
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
  $baseRevId,
  &$redirect
) {
  $topic = "org.fedoraproject.dev.wiki.article.edit";
  $msg = array(
    "user" => $user->getName(),
    "title" => $article->getTitle()->getText(),
  );
  return emit_message($topic, $msg);
}

?>
