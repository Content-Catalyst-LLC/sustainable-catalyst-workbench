<?php
$root=dirname(__DIR__);$plugin=$root.'/wordpress-plugin/sustainable-catalyst-workbench';
$php=file_get_contents($plugin.'/includes/scwb-v533-integration-hardening.php');
$css=file_get_contents($plugin.'/assets/css/sc-workbench-v533.css');
foreach(['viewportScrollGuard','horizontalRailScrollOnly','legacyHomepageShowcaseGuard','v533-interface-status','render_legacy_showcase_guard'] as $m){
    if(strpos($php,$m)===false){fwrite(STDERR,"Missing v5.3.3 runtime marker: $m\n");exit(1);}
}
foreach(['cch-workbench-showcase__inner','cc-home-v4 > .scwb-v533-home','overflow-y: hidden'] as $m){
    if(strpos($css,$m)===false){fwrite(STDERR,"Missing v5.3.3 display marker: $m\n");exit(1);}
}
echo "Workbench v5.3.3 WordPress integration-hardening runtime passed.\n";
