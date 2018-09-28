#!/usr/bin/perl

use LoxBerry::System;
use LoxBerry::Web;
use LoxBerry::Log;

#use File::HomeDir;

#use CGI qw/:standard/;
#use Config::Simple qw/-strict/;
#use warnings;
#use strict;

#my  $home = File::HomeDir->my_home;
#our  $psubfolder;
#my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");

# my $query = new CGI;

#print "hello World";

#foreach (param) {
#	print "Parameter $_ is ";
	
  #print "Parameter $_ is ", param($);
#}

#Set header for our side
my $version = LoxBerry::System::pluginversion();
my $plugintitle = "I/O";
LoxBerry::Web::lbheader("$plugintitle $version", "http://www.loxwiki.eu/display/LOXBERRY/Any+Plugin", "help.html");


# set footer for our side
LoxBerry::Web::lbfooter();

exit;