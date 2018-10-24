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

my $log = LoxBerry::Log->new(name => 'Input_handler',);



LOGSTART("Handle input daemon");

my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");
my $prefix = $pcfg->param("inputs.prefix");

LOGERR "$prefix";

#endless loop
while(1){
	for(my $i=0;$i<$pcfg->param("gpios.inputCount");$i++){
		my $gpio= $pcfg->param("inputs.input$i");
	    
	    my $value = qx {pigs r $gpio};
	    
	    my $response;
	    if($value == 0){
	    		$response = LoxBerry::IO::mshttp_send_mem(1, "$prefix$i", "Off");
	    			
	    } else {
	    		$response = LoxBerry::IO::mshttp_send_mem(1, "$prefix$i", "On");
	    }
	    
		if (! $response) {
		    LOGERR "Error sending to Miniserver $response";
		} else {
		    LOGDEB "Send ok $prefix$i: $value";
		}
	}
	#wenn der Loglevel mehr als Fehler ist (z.b. Debug) wird die Pollzeit aus
	#Sicherheitsgruenden fest auf 1s fest gesetzt 
	if($log->loglevel() >3){
		sleep(1);
	} else {
		sleep (0.1);
	}
	
}

exit;
END
{
    if ($log) {
        $log->LOGEND;
    }
}

