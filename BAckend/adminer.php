<?php
// Download Adminer from: https://www.adminer.org/
// Place this file in a web-accessible directory
// Access via: http://localhost/adminer.php

// Auto-download Adminer
$url = 'https://github.com/vrana/adminer/releases/download/v4.8.1/adminer-4.8.1.php';
$content = file_get_contents($url);
eval('?>' . $content);
?>
