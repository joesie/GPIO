#!/usr/bin/perl

use LoxBerry::System;
use File::HomeDir;

use CGI qw/:standard/;
use Config::Simple qw/-strict/;
use warnings;
use strict;

use LoxBerry::Log;

my $log = LoxBerry::Log->new(name => 'Input_handler',);
LOGSTART("Handle input daemon");

my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");
my $i;

# set up GPIOs as outputs
for($i=0;$i<$pcfg->param("gpios.outputCount");$i++){
  	my $value= $pcfg->param("outputs.output$i");
    system("pigs modes $value w");
}

# set up GPIOs as inputs
for($i=0;$i<$pcfg->param("gpios.inputCount");$i++){
	my $gpio = $pcfg->param("INPUTS.INPUT$i");
    system("pigs modes $gpio r");
    LOGDEB "pigs modes $gpio r";
    # set up input pullups and downs
    my $wiring= $pcfg->param("INPUTS.INPUTWIRING$i");
    if(!$wiring){
		$wiring = "d";
	}
	system("pigs pud $gpio $wiring");
	LOGDEB "pigs pud $gpio $wiring";
}

exit;
END
{
    if ($log) {
        $log->LOGEND;
    }
}