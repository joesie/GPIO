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
my $inputPrefixErrorMessage;
my $inputPrefixErrorClass;

my $cgi = CGI->new;
$cgi->import_names('R');

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
		$pcfg->param("INPUTS.INPUT$currentInputCount", "$inputValue");
		my $result = &validateGpioUserData($inputValue);
		if($result ne("ok")){
			$messagetype = "error";
			$errormessages{"inputs.input$currentInputCount"} = $result;
		}
	}
	for( $currentOutputCount=0; $currentOutputCount< $pcfg->param("gpios.outputCount"); $currentOutputCount++){
		my $outputValue = param("output$currentOutputCount");
		$pcfg->param("outputs.output$currentOutputCount", "$outputValue");
		my $result = &validateGpioUserData($outputValue);
		if($result ne("ok")){
			$messagetype = "error";
			$errormessages{"outputs.output$currentOutputCount"} = $result;
		}
	}
	my $input_prefixLength=length(param('input_prefix'));
	if($input_prefixLength <=0){
		$messagetype = "error";
		$inputPrefixErrorMessage = "Das Feld darf nicht leer sein!";
		$inputPrefixErrorClass = "error";
	}
	$pcfg->param("INPUTS.PREFIX", param('input_prefix'));
  	$pcfg->param("INPUTS.INPUTSAMPLINGRATERATE", param('input_samplingrate'));
  	$pcfg->param("MAIN.MINISERVER", param('selMiniServer'));
  
	if($messagetype ne("error")){
		$pcfg->save();
  		system($^X, "$lbpbindir/inoutpinconfig.pl");
  		$message = "Eingaben wurden erfolgreich gespeichert";
  		$messagetype = "info";
	} else{
		$message = "Fehler beim Speichern. Bitte die Eingaben überprüfen!";
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

# ---------------------------------------------------
# Control for "samplingrate" Dropdown
# ---------------------------------------------------
sub samplingRates{
  	my @result;
  	my @values  = (0.05,0.1,0.25,0.5);


	my $default = $pcfg->param("INPUTS.INPUTSAMPLINGRATERATE");
	my $selected = "";
	
	foreach my $value (@values) {
   		$selected = "";
   		if($value == $default){
   			$selected = 'selected';
   		}
   		my $label = $value * 1000; 
   		push @result, {VALUE=>$value, LABEL=>"$label ms" ,CHOOSED=>$selected};
	}
	if(1 == $default){
   		$selected = 'selected';
    }
  	push @result, {VALUE=>1, LABEL=>"1s" ,CHOOSED=>$selected};
  	
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

# ---------------------------------------------------
# Control for "selMiniServer" Dropdown
# ---------------------------------------------------
 
my %miniservers = LoxBerry::System::get_miniservers();
my @miniserverarray;
my %miniserverhash;

foreach my $ms (sort keys %miniservers)
{
    push @miniserverarray, "$ms";
    $miniserverhash{"$ms"} = $miniservers{$ms}{Name};

}
 
my $selMiniServer = $cgi->popup_menu(
      -name    => 'selMiniServer',
      -values  => \@miniserverarray,
      -labels  => \%miniserverhash,
      -default => $pcfg->param('MAIN.DEFAULT.MINISERVER'),
  );
 

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
my @inputConfigArray = &createInputOutputConfig($pcfg->param("gpios.inputCount"), "INPUTS.INPUT");
$template->param("number_of_inputs" => \@inputConfigArray);
$template->param("MESSAGE" =>$message);
$template->param("MESSAGETYPE" => $messagetype);
$template->param("input_prefix" => $pcfg->param("INPUTS.PREFIX"));
$template->param("input_prefix_error_message" => $inputPrefixErrorMessage);
$template->param("input_prefix_error_class" => $inputPrefixErrorClass);

my @samplingRates = &samplingRates();
$template->param("input_samplingrate" => \@samplingRates);

$template->param( "selMiniServer" => $selMiniServer );

# Write template
print $template->output();

print LoxBerry::Web::logfile_button_html( NAME => 'Input_handler' );

# set footer for our side
LoxBerry::Web::lbfooter();

exit;
