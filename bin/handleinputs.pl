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

# my $log = Loxberry::Log::new(name => 'Input_handler');

# LOGSTART("Daemon gestartet");

my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");


#endless loop
while(1){
	for(my $i=0;$i<$pcfg->param("gpios.inputCount");$i++){
		my $gpio= $pcfg->param("inputs.input$i");
	    
	    my $value = qx {pigs r $gpio};
	    
	    my $response;
	    if($value == 0){
	    		$response = LoxBerry::IO::mshttp_send_mem(1, "input$i", "Off");
	    			
	    } else {
	    		$response = LoxBerry::IO::mshttp_send_mem(1, "input$i", "On");
	    }
	   # LOGDEB "Response: $response value: $value";
	    
		if (! $response) {
#		    LOGDEB "Error sending to Miniserver";
		} else {
#		    LOGDEB "Send ok";
		}
	}
	
	sleep (0.1);
}

exit;
#END
#{
#    if ($log) {
#        $log->LOGEND;
#    }
#}

