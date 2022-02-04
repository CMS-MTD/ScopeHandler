#include <string>
#include <sys/types.h>
#include <sys/stat.h>
#include <fstream> 
#include <iostream> 
#include <sstream>
#include <fstream>
#include "TROOT.h"
#include <TStyle.h>
#include "TTree.h"
#include "TFile.h"
#include "TLatex.h"
#include "TCanvas.h"
#include "TH1F.h"
#include <iomanip>
using namespace std;

#ifdef __MAKECINT__
#pragma link C++ class std::vector < std::vector<int> >+;
#pragma link C++ class std::vector < std::vector<float> >+;
#endif

const unsigned int NUM_CHANNELS = 8;
const unsigned int NUM_TIMES = 1;
const unsigned int NUM_SAMPLES = 50000002;

// To do
// Noise calculation
// config file for each channel
// add branches

bool Condor = true;

// TString inputDir="/home/daq/ScopeData/LecroyConverted/";
// TString configDir="/home/daq/LecroyControl/HitCounter/configs/";

// TString inputDir="/home/daq/SurvivalBeam2021/LecroyScope/RecoData/ConversionRECO/";
// TString inputFileFormat="converted_run";

// TString outputDir="/home/daq/SurvivalBeam2021/LecroyScope/RecoData/HitCounterRECO/RecoWithoutTracks/";
// TString outputFileFormat="hitTree_run";

//Condor
TString configDir="";

TString inputDir="";
TString inputFileFormat="converted_run";

TString outputDir="";
TString outputFileFormat="hitTree_run";




// Output root file
TFile *file;
TTree *tree;
       
//Output branches
int scopechan;
float amp;
double hit_time;
float integral;
float tot;
int nsamples_above_thresh;
int sample_start;
float time_since_previous_hit;


//Input file and branches
TFile* file_in;
TTree* tree_in;
int runNumber;
int configVersion;
double sample_width=0;

float** vertical_axes= new float*[NUM_CHANNELS];
double** time_axes = new double*[NUM_TIMES];
float* timeoffsets = new float[NUM_CHANNELS];

double* AUX_time = new double[NUM_TIMES*NUM_SAMPLES];
float* AUX_channel = new float[NUM_CHANNELS*NUM_SAMPLES];

float channel_polarity[8] = {-1,-1,-1,1,
							-1,-1,-1,-1}; 

///// Hit defining parameters   /////
float tot_thres[8];//=10; //mV. Threshold for measuring ToT

float threshold[8] = {10,10,10,10,10,10,10,10};// = 10; //mV. Threshold for detecting a new hit
float endthreshold[8]={10,10,10,10,10,10,10,10};;//= 8; //mV. Threshold for defining end of a hit
int nconsec[8]={4,4,4,4,4,4,4,4};// = 4; //Number of consecutive samples that must be over threshold to register a hit
int nconsecEnd[8]={4,4,4,4,4,4,4,4};// = 4; //Number of consecutive samples that must be within endthreshold of 0 to end pulse

int samples_before=20; //Number of samples before pulse to consider.
int samples_after=20; //Number of samples after pulse to consider.


int displays_to_print_per_channel = 15;
int already_printed[NUM_CHANNELS];
//////////////////////////////

void readConfigFile();
void loadInputFile(TString inFileName);
void prepareOutputTree(TString outFileName);
void printSegment(TH1F * h, int start_sample,int chan);
void registerHit(int start_sample, int end_sample, int chan, int prev_hit_peak_sample);
void processChannel(int chan);


int main(int argc, char **argv)
{
	runNumber = stoi(argv[1]);
	configVersion = stoi(argv[2]);

	//Load config
	// readConfigFile();
	cout<<"threshold 5 " <<threshold[5]<<endl;
	cout<<"threshold 6 " <<threshold[6]<<endl;
	cout<<"nconsec 3 " <<nconsec[3]<<endl;


	//Load input
	TString inFileName = Form("%s%s%i.root",inputDir.Data(),inputFileFormat.Data(),runNumber);
	loadInputFile(inFileName);
	float duration = time_axes[0][NUM_SAMPLES-1] - time_axes[0][0];
	cout<<"Run number: "<< runNumber<<", duration: "<<duration<<" s"<<endl;
	sample_width = time_axes[0][2] - time_axes[0][1];
	cout<<"Sample width: "<<sample_width<<" s"<<endl;
	//Make output tree
	TString outFileName = Form("%s/v%i/%s%i.root",outputDir.Data(),configVersion,outputFileFormat.Data(),runNumber);
	if (Condor) outFileName = Form("%s%i.root",outputFileFormat.Data(),runNumber);
	prepareOutputTree(outFileName);
	gStyle->SetGridStyle(3);
	gStyle->SetGridColor(14);
	//Process channels
	for(int ichan=0;ichan<NUM_CHANNELS;ichan++){
		processChannel(ichan);
	}

	float hits_chan1 = tree->GetEntries("scopechan==3");

	cout<<"Rate in channel index 3: "<<hits_chan1/duration<<" Hz"<<endl;
	// tree->Fill();
	tree->Write();
	file->Close();
}


void readConfigFile(){
	TString configFileName = Form("%s/config%i.txt",configDir.Data(),configVersion);
	if(Condor) configFileName = Form("config%i.txt",configVersion);
	std::ifstream input(configFileName.Data());
	string str;
	if(input){
	int iteration=0;
	while (std::getline(input, str))
	{
	    if (str.length() ){
	        std::cout << str << std::endl;
	        if(iteration>0){
	        	vector<int> result;
	        	stringstream s_stream(str); //create string stream from the string
	        	while(s_stream.good()) {
	        	   string substr;
	        	   getline(s_stream, substr, ','); //get first string delimited by comma
	        	   result.push_back(std::stoi(substr));
	        	}
	        
	        	threshold[iteration-1] = result[0];
	        	endthreshold[iteration-1] = result[1];
	        	tot_thres[iteration-1] = result[2];
	        	nconsec[iteration-1] = result[3];
	        	nconsecEnd[iteration-1] = result[4];

	        }
	    }

	    iteration++;
	}
}
else{ cout<<"Error, can't find config: "<<configFileName<<endl;}
}

void printSegment(TH1F * h, int start_sample,int end_sample, int chan){
	TCanvas * c1 = new TCanvas(Form("c1_%i",start_sample),"",1200,600);
	gPad->SetRightMargin(0.27);
	h->SetLineWidth(2);


	//remap time axis to simplify plot
	int nbins = h->GetNbinsX();
	float start_time = 0;
	float end_time =  1e9*nbins*sample_width;

	TH1F * h_remap = new TH1F(Form("wave_%i",start_sample),"",nbins,start_time,end_time);
		for(int is=1; is<=nbins;is++){
		// cout<<setprecision(10)<<h->GetBinCenter(is)<<endl;
		h_remap->SetBinContent(is,h->GetBinContent(is));
	}

	h_remap->SetMarkerStyle(20);
	// h_remap->SetMarkerSize(2);
	c1->SetGridx();
	c1->SetGridy();
	gStyle->SetOptStat(1111111);
	h_remap->SetTitle(Form("Chan %i, hit time %0.9f s; Time [ns]; Voltage [mV]",chan, time_axes[0][start_sample]));

	h_remap->Draw("lp");

	TLatex tla;
	tla.SetTextSize(0.045);
	tla.SetTextFont(42);

	tla.DrawLatexNDC(0.75,0.58,Form("Amp: %0.2f mV",amp));
	tla.DrawLatexNDC(0.75,0.53,Form("Integral: %0.0f mVs",integral));
	tla.DrawLatexNDC(0.75,0.48,Form("Duration: %0.2f ns",tot));
	tla.DrawLatexNDC(0.75,0.43,Form("Time: %0.2f ns",1e9*(hit_time-time_axes[0][start_sample])));
	tla.DrawLatexNDC(0.75,0.38,Form("Samples above thres: %i",nsamples_above_thresh));


	c1->Print(Form("displays/run%i_chan%i_sample_%i.pdf",runNumber,chan,start_sample));
	// c1->Print(Form("displays/chan_%i_sample_%i.root",chan,start_sample));

}

void registerHit(int start_sample, int end_sample, int chan, int prev_hit_peak_sample){

	TH1F * h = new TH1F(Form("h_%i",start_sample),"",end_sample-start_sample+1,time_axes[0][start_sample],time_axes[0][end_sample]);
	for(int is=start_sample; is<=end_sample;is++){
		h->SetBinContent(is - start_sample +1,channel_polarity[chan]*1000.*vertical_axes[chan][is]);
	}

	sample_start = start_sample;
	scopechan = chan;
	amp = h->GetMaximum();
	int maxbin =0;
	h->GetBinWithContent(amp,maxbin);
	hit_time = h->GetBinCenter(maxbin);
	integral = h->Integral();


	time_since_previous_hit = hit_time - time_axes[0][prev_hit_peak_sample];

	tot=0;
	for(int is=maxbin;is>0;is--){
		if(h->GetBinContent(is) > tot_thres[chan]){tot++;}
		else break;
	}
	for(int is=maxbin;is<=h->GetNbinsX();is++){
		if(h->GetBinContent(is) > tot_thres[chan]){tot++;}
		else break;
	}

	tot *= 1e9*sample_width;


	//Number of samples outside threshold in entire few ns window (noise rejection)
	nsamples_above_thresh=0;
	for(int is=1;is<h->GetNbinsX()+1;is++){
		if(fabs(h->GetBinContent(is)) > tot_thres[chan]){nsamples_above_thresh++;}
	}

	tree->Fill();
	if(already_printed[chan]<displays_to_print_per_channel){
		printSegment(h, start_sample,end_sample,chan);
		already_printed[chan]++;
	}

}
void processChannel(int chan){

	bool inpulse = false;
	int nover = 0; // Number of samples seen consecutively over threshold
	int nunder = 0; // Number of samples seen consecutively under threshold
	int i_begin=0;

	float local_max=0;
	int sample_of_local_max=0;
	int previous_hit_sample_of_local_max=0;

	for(uint isample = 0;isample<NUM_SAMPLES;isample++){
		float this_sample = channel_polarity[chan]*1000.*vertical_axes[chan][isample];
		
		if(!inpulse){ //Not within a pulse yet
			if(this_sample > threshold[chan]){ //above threshold, start counting
				nover++;
				if(this_sample > local_max) {
					local_max= this_sample;
					sample_of_local_max = isample;
				}
			}
			else{ //below threshold, reset counters
				nover=0;
				i_begin=isample; // store most recent sample below threshold, currently not used
			}

			if(nover>=nconsec[chan]){ //Reached enough samples above threshold to define a new hit.
				inpulse=true;
				nunder=0;
				
			}
		}//not in pulse
		else{ //in a pulse, now looking to end the pulse.

			if(fabs(this_sample)<endthreshold[chan] || fabs(this_sample) <0.1*local_max ) nunder++;
			else {
				nunder=0;
				if(this_sample > local_max) {
					local_max= this_sample;
					sample_of_local_max = isample;
				}
			}

			if(nunder>=nconsecEnd[chan]){ //Found enough low samples to end pulse and start looking for next one. Reset counters
				inpulse = false; // End the pulse
				nover = 0;
				nunder = 0;
				
				// registerHit(sample_of_local_max-samples_before,sample_of_local_max+samples_after,chan,previous_hit_sample_of_local_max);
				registerHit(i_begin-samples_before,isample+samples_after,chan,previous_hit_sample_of_local_max);
				
				previous_hit_sample_of_local_max = sample_of_local_max;
				local_max=0;
				sample_of_local_max=0;
				i_begin = isample;
			}
		}
	}
}

void prepareOutputTree(TString outFileName){
	file = new TFile(outFileName,"recreate");
	tree = new TTree("hits","hits");

	TBranch * b_scopechan = tree->Branch("scopechan",&scopechan,"scopechan/I");
    tree->SetBranchAddress("scopechan",&scopechan,&b_scopechan);

    TBranch * b_amp = tree->Branch("amp",&amp,"amp/F");
    tree->SetBranchAddress("amp",&amp,&b_amp);

    TBranch * b_time = tree->Branch("time",&hit_time,"time/D");
    tree->SetBranchAddress("time",&hit_time,&b_time);

    TBranch * b_tot = tree->Branch("tot",&tot,"tot/F");
    tree->SetBranchAddress("tot",&tot,&b_tot);

	TBranch * b_nsamples_above_thresh = tree->Branch("nsamples_above_thresh",&nsamples_above_thresh,"nsamples_above_thresh/I");
    tree->SetBranchAddress("nsamples_above_thresh",&nsamples_above_thresh,&b_nsamples_above_thresh);

    TBranch * b_integral = tree->Branch("integral",&integral,"integral/F");
    tree->SetBranchAddress("integral",&integral,&b_integral);

	TBranch * b_sample_start = tree->Branch("sample_start",&sample_start,"sample_start/I");
    tree->SetBranchAddress("sample_start",&sample_start,&b_sample_start);

    TBranch * b_time_since_previous_hit = tree->Branch("time_since_previous_hit",&time_since_previous_hit,"time_since_previous_hit/F");
    tree->SetBranchAddress("time_since_previous_hit",&time_since_previous_hit,&b_time_since_previous_hit);



}

void loadInputFile(TString inFileName){
	for(unsigned int ic=0; ic<NUM_CHANNELS; ic++)
	{
	   vertical_axes[ic] = &(AUX_channel[ic*NUM_SAMPLES]);
	   if(ic<NUM_TIMES) time_axes[ic] = &(AUX_time[ic*NUM_SAMPLES]);
	}

	file_in = TFile::Open(inFileName, "READ");
	tree_in = (TTree*)file_in->Get("pulse"); 

	// tree_in->Print();
	// cout<<"Got "<<tree_in->GetEntries()<<" entries."<<endl;
	tree_in->SetBranchAddress("channel",&(vertical_axes[0][0]));
	tree_in->SetBranchAddress("time",&(time_axes[0][0]));
	tree_in->SetBranchAddress("timeoffsets",&(timeoffsets[0]));

	tree_in->GetEntry(0);

	// for(int ic=0;ic<8;ic++){
	// 	cout<<"offset "<<timeoffsets[ic]<<endl;
	// }
	// for(int ic=0;ic<8;ic++){
	// 	cout<<"time "<<setprecision(10)<<time_axes[0][ic]<<endl;
	// }

}