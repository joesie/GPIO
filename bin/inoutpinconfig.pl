#!/usr/bin/perl

use LoxBerry::System;
use File::HomeDir;

use CGI qw/:standard/;
use Config::Simple qw/-strict/;
use warnings;
use strict;
#use LoxBerry::Log;

#my $log = Loxberry::Log::new(name => 'GPIO_Config');
#LOGSTART "Daemon started";

my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");
my $i;

for($i=0;$i<$pcfg->param("gpios.outputCount");$i++){
  	my $value= $pcfg->param("outputs.output$i");
    system("pigs modes $value w");
 #   LOGINF "Configure GPIO$value as output";
}

for($i=0;$i<$pcfg->param("gpios.inputCount");$i++){
	my $value= $pcfg->param("inputs.input$i");
    system("pigs modes $value r");
    
  #  LOGINF "Configure GPIO$value as input";
}


exit;
END
{
   # if ($log) {
    #    $log->LOGEND;
    #}
}