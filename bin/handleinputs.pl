#!/usr/bin/perl

use LoxBerry::System;
use File::HomeDir;

use CGI qw/:standard/;
use Config::Simple qw/-strict/;
use warnings;
use strict;
use LoxBerry::IO;
use LoxBerry::Log;
use Time::HiRes qw ( sleep );

notify( $lbpplugindir, "daemon", "Start input handler daemon");


my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");

#endless loop
while(1){
	for($i=0;$i<$pcfg->param("gpios.inputCount");$i++){
		my $gpio= $pcfg->param("inputs.input$i");
	    
	    my $value = system("pigs modes $gpio r");
	    notify( $lbpplugindir, "daemon", "Send value to ms $value");
	    my $response;
	    if($value == 1){
	    		$response = mshttp_send_mem(1, "input$i", "On");	
	    } else {
	    		$response = mshttp_send_mem(1, "input$i", "Off");
	    }
	    notify( $lbpplugindir, "daemon", "Response: $response");
	    
		if (! $response) {
		    print STDERR "Error sending to Miniserver";
		} else {
		    print STDERR "Sent ok.";
		}
	}
	
	sleep (0.1);
}


exit;
