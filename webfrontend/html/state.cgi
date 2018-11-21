#!/usr/bin/perl

use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::Log;
use File::HomeDir;
use CGI qw/:standard/;  
use strict;
use warnings;
use JSON;

my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");
my $json = JSON->new;

my %jsonData;

for( my $currentOutputCount=0; $currentOutputCount< $pcfg->param("gpios.outputCount"); $currentOutputCount++){
	my $gpio= $pcfg->param("OUTPUTS.OUTPUT$currentOutputCount");    
	my $value = qx {pigs r $gpio};
	my $formatValue = $value == 1 ? 'true' : 'false';
	
	$jsonData{"o".$currentOutputCount} = $formatValue;	
}

my $data_to_json = {output=>{\%jsonData}};


print "Status: 200 OK\r\n";
print "Content-Type: application/json\r\n\r\n";
print $json->encode($data_to_json) . "\n";


exit 0;

