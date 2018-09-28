#!/usr/bin/perl

use LoxBerry::System;
use LoxBerry::Web;
use File::HomeDir;

use CGI qw/:standard/;
use Config::Simple qw/-strict/;
use warnings;
use strict;

use IPC::System::Simple qw(system capture);

my  $home = File::HomeDir->my_home;
our  $psubfolder;
my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");


# Figure out in which subfolder we are installed
$psubfolder = abs_path($0);
$psubfolder =~ s/(.*)\/(.*)\/(.*)$/$2/g;


# Save settings
if ( param('saveCount') ) {
  my $outputCount = param('output_count');
  my $inputCount = param('input_count');

  $pcfg->param("gpios.inputCount", "$inputCount");
  $pcfg->param("gpios.outputCount", "$outputCount");
  
  $pcfg->save();
  
}


# Save settings
if ( param('saveIoConfig') ) {
	my $currentInputCount;
	my $currentOutputCount;
	
	for($currentInputCount=0; $currentInputCount< $pcfg->param("gpios.inputCount"); $currentInputCount++){
		my $inputValue = param("input$currentInputCount");
		$pcfg->param("inputs.input$currentInputCount", "$inputValue");
	}
	for( $currentOutputCount=0; $currentOutputCount< $pcfg->param("gpios.outputCount"); $currentOutputCount++){
		my $outputValue = param("output$currentOutputCount");
		$pcfg->param("outputs.output$currentOutputCount", "$outputValue");
	}
	
	$pcfg->save();
	
  	system($^X, "$home/bin/plugins/io/inoutpinconfig.pl");
  	
}



##
#Parameter the selected option
##
sub createSelectArray{
  my @result;
  my $i;
  my $selected ="";

  for($i=0;$i<=15;$i++){
      $selected = "";
      if($i == $_[0]){
        $selected = 'selected';
      } 
      push @result, {COUNT=>$i, CHOOSED=>$selected};
  }
  return @result;
}

##
# Parameter for I/O config
# @Parameter: first: number of inputs or outputs, second: the string to configfile for stored value
##
sub createInputOutputConfig{
  my @result;
  my $i;

  for($i=0;$i<$_[0];$i++){
  	my $value= $pcfg->param("$_[1]$i");
    push @result, {current=>$i,value =>$value};
  }
  return @result;
}

##
#handle Template and render index page
##

#Set header for our side
my $version = LoxBerry::System::pluginversion();
my $plugintitle = "I/O";
LoxBerry::Web::lbheader("$plugintitle $version", "http://www.loxwiki.eu/display/LOXBERRY/Any+Plugin", "help.html");

#Load Template and fill with given parameters
my $template = HTML::Template->new(filename => "$lbptemplatedir/main.html");

my @outputSelectArray = &createSelectArray($pcfg->param("gpios.outputCount"));
$template->param("SELECT_OUTPUT_COUNT" => \@outputSelectArray);
my @inputSelectArray = &createSelectArray($pcfg->param("gpios.inputCount"));
$template->param("select_input_count" => \@inputSelectArray);

my @outputConfigArray = &createInputOutputConfig($pcfg->param("gpios.outputCount"), "outputs.output");
$template->param("number_of_outputs" => \@outputConfigArray);
my @inputConfigArray = &createInputOutputConfig($pcfg->param("gpios.inputCount"), "inputs.input");
$template->param("number_of_inputs" => \@inputConfigArray);


# Write template
print $template->output();

# set footer for our side
LoxBerry::Web::lbfooter();

exit;