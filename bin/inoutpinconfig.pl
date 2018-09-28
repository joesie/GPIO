#!/usr/bin/perl

use LoxBerry::System;
use File::HomeDir;

use CGI qw/:standard/;
use Config::Simple qw/-strict/;
use warnings;
use strict;


my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");
my $i;

for($i=0;$i<$pcfg->param("gpios.outputCount");$i++){
  	my $value= $pcfg->param("outputs.output$i");
    system("pigs modes $value w");
    
}

for($i=0;$i<$pcfg->param("gpios.inputCount");$i++){
	my $value= $pcfg->param("inputs.input$i");
    system("pigs modes $value r");
}


exit;