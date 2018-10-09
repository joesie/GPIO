#!/usr/bin/perl

use LoxBerry::System;
use LoxBerry::Web;
use File::HomeDir;

use CGI qw/:standard/;
use Config::Simple qw/-strict/;
use warnings;
use strict;

use IPC::System::Simple qw(system capture);

my $pcfg = new Config::Simple("$lbpconfigdir/pluginconfig.cfg");
my $message;
my $messagetype;
my %errormessages;




##
# validate Userdata 
##
sub validateGpioUserData{
	my $value= $_[0];
	
	if($value eq("")){
		return "Feld darf nicht leer sein!";
	}
	
	if ($value !~ /^\d+?$/) {
		return "Nur Zahlen sind erlaubt";
	}
	
	if($value > 27 || $value < 2){
		return "Nur Werte zwischen 2 und 27 sind erlaubt!";
	}
	return "ok";
}


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
		my $result = &validateGpioUserData($inputValue);
		if($result ne("ok")){
			$messagetype = "error";
			$message = "Fehler beim Speichern. Bitte die Eingaben überprüfen!";
			$errormessages{"inputs.input$currentInputCount"} = $result;
		}
	}
	for( $currentOutputCount=0; $currentOutputCount< $pcfg->param("gpios.outputCount"); $currentOutputCount++){
		my $outputValue = param("output$currentOutputCount");
		$pcfg->param("outputs.output$currentOutputCount", "$outputValue");
		my $result = &validateGpioUserData($outputValue);
		if($result ne("ok")){
			$messagetype = "error";
			$message = "Fehler beim Speichern. Bitte die Eingaben überprüfen!";
			$errormessages{"outputs.output$currentOutputCount"} = $result;
		}
	}
	
	if($messagetype ne("error")){
		$pcfg->save();
  		system($^X, "$lbpbindir/inoutpinconfig.pl");
  		$message = "Eingaben wurden erfolgreich gespeichert";
  		$messagetype = "info";
	}
	
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
  	my $error = $errormessages{"$_[1]$i"};
  	my $class = "info";;
  	if($error ne ""){
  		$class = "error";
  	}
    push @result, {current=>$i,value =>$value, errormessage=>$error, class=>$class};
  }
  return @result;
}

##
#handle Template and render index page
##

#Set header for our side
my $version = LoxBerry::System::pluginversion();
my $plugintitle = "GPIO";
our $htmlhead = "<link rel='stylesheet' href='style.css'></link>";

LoxBerry::Web::lbheader("$plugintitle $version", "https://www.loxwiki.eu/pages/viewpage.action?pageId=39355014", "help.html");

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
$template->param("MESSAGE" =>$message);
$template->param("MESSAGETYPE" => $messagetype);


# Write template
print $template->output();

# set footer for our side
LoxBerry::Web::lbfooter();

exit;