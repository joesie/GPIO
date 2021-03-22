#!/usr/bin/perl

use LoxBerry::System;
use LoxBerry::Web;
use File::HomeDir;
use LoxBerry::Log;
use LoxBerry::IO;

use CGI qw/:standard/;
use warnings;
use strict;

use IPC::System::Simple qw(system capture);
use LoxBerry::JSON;

my $message;
my $messagetype;
my %errormessages;
my $inputPrefixErrorMessage;
my $inputPrefixErrorClass;

my $log = LoxBerry::Log->new(name => 'CGI',);
LOGSTART("GPIO CGI Log");

my $cfgfile = "$lbpconfigdir/pluginconfig.json";
LOGINF $cfgfile;

my $jsonobj = LoxBerry::JSON->new();
my $pcfg = $jsonobj->open(filename => $cfgfile);
if (!$pcfg) {
	LOGERR "No configfile found";
	exit;
}


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

  $pcfg->{gpio}->{inputs}->{count} = "$inputCount";
  $pcfg->{gpio}->{outputs}->{count}= "$outputCount";
  my $saved = $jsonobj->write();
  LOGINF "Configuration saved $saved";
}

#==============
# Save settings
#==============
if ( param('saveIoConfig') ) {
	my $currentInputCount;
	my $currentOutputCount;

# Handle input settings
	for($currentInputCount=0; $currentInputCount< $pcfg->{gpio}->{inputs}->{count}; $currentInputCount++){
		my $inputValue = param("input$currentInputCount");
		my $wiringValue = param("INPUTS.INPUTWIRING$currentInputCount");

		$pcfg->{gpio}->{inputs}->{"channel_$currentInputCount"}->{pin} = "$inputValue";
		$pcfg->{gpio}->{inputs}->{"channel_$currentInputCount"}->{wiring} = "$wiringValue";

		my $result = &validateGpioUserData($inputValue);
		if($result ne("ok")){
			$messagetype = "error";
			$errormessages{"inputs.pin$currentInputCount"} = $result;
		}
	}

# handle output settings
	for( $currentOutputCount=0; $currentOutputCount< $pcfg->{gpio}->{outputs}->{count}; $currentOutputCount++){
		my $outputValue = param("output$currentOutputCount");

		$pcfg->{gpio}->{outputs}->{"channel_$currentOutputCount"}->{pin} = "$outputValue";
		my $result = &validateGpioUserData($outputValue);
		if($result ne("ok")){
			$messagetype = "error";
			$errormessages{"outputs.pin$currentOutputCount"} = $result;
		}
	}

  $pcfg->{main}->{miniserver} = param('selMiniServer');

	if($messagetype ne("error")){

		my $saved = $jsonobj->write();
		LOGINF "Configuration saved $saved";

		system("$lbpbindir/wrapper.sh restart > /dev/null 2>&1");
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
	my $default = $pcfg->{main}->{samplingrate};
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

		my $value = $pcfg->{gpio}->{"$_[1]"}->{"channel_$i"}->{pin};
  	my $error = $errormessages{"$_[1].pin$i"};
  	my $class = "info";;
  	if($error ne ""){
  		$class = "error";
  	}

    if($_[1] eq "outputs"){
  		push @result, {current=>$i,value =>$value, errormessage=>$error, class=>$class};
  	} else {
			# for inputs need to configure the wiring Dropdown
			my $wiring=     $pcfg->{gpio}->{"$_[1]"}->{"channel_$i"}->{wiring};
			my $confwiring= $pcfg->{gpio}->{"$_[1]"}->{"channel_$i"}->{wiring};
			my @wiring = ('d', 'u' );
			my %wiringlabels = (
					'd' => 'Pulldown',
					'u' => 'Pullup',
			);
			my $wiringselectlist = $cgi->popup_menu(
					-id	=> 'INPUTS.INPUTWIRING' . $i,
					-name    => 'INPUTS.INPUTWIRING' . $i,
					-values  => \@wiring,
					-labels  => \%wiringlabels,
					-default => $confwiring,
			);
  		push @result, {current=>$i,value =>$value, errormessage=>$error, class=>$class, SELECTLIST =>$wiringselectlist};
  	}
  }
  return @result;
}

##
#handle Template and render index page
##
# handle MQTT details
my $mqttsubscription = LoxBerry::System::lbhostname() . "/gpio/#";
my $mqttcred = LoxBerry::IO::mqtt_connectiondetails();
my $mqtthint = "Alle Daten werden per MQTT übertragen. Die Subscription dafür lautet <span class='mono'>
								$mqttsubscription</span> und wird im MQTT Gateway Plugin automatisch eingetragen.";
my $mqtthintclass = "hint";

if(!$mqttcred){
	$mqtthint = "MQTT Gateway Plugin wurde nicht gefunden oder ist nicht konfiguriert.
								Das GPIO Plugin funktioniert nur mit korrekt insatlliertem MQTT Gateway Plugin";
	$mqtthintclass = "notityRedMqtt";
}


#Set header for our side
my $version = LoxBerry::System::pluginversion();
my $plugintitle = "GPIO";
our $htmlhead = "<link rel='stylesheet' href='style.css'></link>";

LoxBerry::Web::lbheader("$plugintitle $version", "https://www.loxwiki.eu/pages/viewpage.action?pageId=39355014", "help.html");

#Load Template and fill with given parameters
my $template = HTML::Template->new(filename => "$lbptemplatedir/main.html");

my @outputSelectArray = &createSelectArray($pcfg->{gpio}->{outputs}->{count});
$template->param("SELECT_OUTPUT_COUNT" => \@outputSelectArray);
my @inputSelectArray = &createSelectArray($pcfg->{gpio}->{inputs}->{count});
$template->param("select_input_count" => \@inputSelectArray);

my @outputConfigArray = &createInputOutputConfig($pcfg->{gpio}->{outputs}->{count}, "outputs");
$template->param("number_of_outputs" => \@outputConfigArray);
my @inputConfigArray = &createInputOutputConfig($pcfg->{gpio}->{inputs}->{count}, "inputs");
$template->param("number_of_inputs" => \@inputConfigArray);
$template->param("MESSAGE" =>$message);
$template->param("MESSAGETYPE" => $messagetype);
$template->param("mqtthint" => $mqtthint);
$template->param("mqtthintclass" => $mqtthintclass);




# Write template
print $template->output();

# set footer for our side
LoxBerry::Web::lbfooter();

exit;
END
{
    if ($log) {
        $log->LOGEND;
    }
}
