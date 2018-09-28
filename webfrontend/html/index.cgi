#!/usr/bin/perl

use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::Log;
use File::HomeDir;
use CGI qw/:standard/;  
use strict;
use warnings;

my $buf;

my  $home = File::HomeDir->my_home;
my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");


my $query = new CGI;




my @names = $query->param;
my $name;
my $result = 0;
foreach $name ( @names ) {
	if (  $name =~ /\_/ ) { 
        next;
    } else {
        my $currentResult = &swichChannel($name, $query->param($name));
        if($currentResult < 0){
        		$result = $currentResult;
        }
    }
}
  
sub swichChannel{
	my $name = $_[0];
	my $value = $_[1];
	
	
	if(substr($name, 0, 1) ne "o"){
		$buf .="<p>The given parameter $name is not allowed! Please check your parameter config!</p>";
		return -1;
	}
	if(length($value) <= 1){
		$buf .="<p> The value from parameter $name is too short! Please check your parameter config!</p>";
		return -1;
	}
	
	my $channel = substr($name, 1, 3);
	my $gpio= $pcfg->param("outputs.output$channel");
	
	if($value eq("on")){
		system("pigs w $gpio 1");
	}else{
		system("pigs w $gpio 0");
	}
	return 0;
}


if($result >= 0){
	print "Status: 200 OK\r\n";
	print "Content-Type: text/plain\r\n\r\n";
} else {
	print "Status: 400 Bad Request\r\n";
	print "Content-Type: text/html\r\n\r\n";
	print "<h2> 400 Bad Request</h2>";
	print $buf;	
}



exit (0);

