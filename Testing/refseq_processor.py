#!/usr/bin/env python

import pyhive

from collections import OrderedDict
import urllib2
import ftplib
from StringIO import StringIO
import os
import gzip
import subprocess
import linecache
import sys
import re
from Bio import SeqIO
from Bio import Seq
from Bio import SeqUtils
from Bio.Seq import MutableSeq
import math
import time
import email.utils # for RFC 1123 timestamp parsing
from bs4 import BeautifulSoup # for NCBI html table directory listing parsing
import distutils.spawn # for find_executable

genbank_divisions = ["gbbct", "gbinv", "gbmam", "gbphg", "gbpln", "gbpri", "gbrod", "gbvrl", "gbvrt"]
refseq_divisions = ["archaea", "bacteria", "fungi", "invertebrate", "plant", "protozoa", "vertebrate_mammalian", "vertebrate_other", "viral"]

genbank_weights = {"gbbct": 1, "gbinv": 1, "gbmam": 1, "gbphg": 1, "gbpln": 1, "gbpri": 1, "gbrod": 1, "gbvrl": 1, "gbvrt": 1}
refseq_weights = {"archaea": 10, "bacteria": 10, "fungi": 1000, "invertebrate": 500, "plant": 1000, "protozoa": 500, "vertebrate_mammalian": 1000, "vertebrate_other": 1000, "viral": 5}

CodonsDict = OrderedDict([('TTT', 0), ('TTC', 0), ('TTA', 0), ('TTG', 0), ('CTT', 0),
                          ('CTC', 0), ('CTA', 0), ('CTG', 0), ('ATT', 0), ('ATC', 0),
                          ('ATA', 0), ('ATG', 0), ('GTT', 0), ('GTC', 0), ('GTA', 0),
                          ('GTG', 0), ('TAT', 0), ('TAC', 0), ('TAA', 0), ('TAG', 0),
                          ('CAT', 0), ('CAC', 0), ('CAA', 0), ('CAG', 0), ('AAT', 0),
                          ('AAC', 0), ('AAA', 0), ('AAG', 0), ('GAT', 0), ('GAC', 0),
                          ('GAA', 0), ('GAG', 0), ('TCT', 0), ('TCC', 0), ('TCA', 0),
                          ('TCG', 0), ('CCT', 0), ('CCC', 0), ('CCA', 0), ('CCG', 0),
                          ('ACT', 0), ('ACC', 0), ('ACA', 0), ('ACG', 0), ('GCT', 0),
                          ('GCC', 0), ('GCA', 0), ('GCG', 0), ('TGT', 0), ('TGC', 0),
                          ('TGA', 0), ('TGG', 0), ('CGT', 0), ('CGC', 0), ('CGA', 0),
                          ('CGG', 0), ('AGT', 0), ('AGC', 0), ('AGA', 0), ('AGG', 0),
                          ('GGT', 0), ('GGC', 0), ('GGA', 0), ('GGG', 0)])  # initialize w/ acceptable keys

NuclDict = OrderedDict([("A", 0), ("T", 0), ("C", 0), ("G", 0)])

def pull_filelists_ncbi():
    genbank_filelists = {"gbbct": [], "gbinv": [], "gbmam": [], "gbphg": [], "gbpln": [], "gbpri": [], "gbrod": [], "gbvrl": [], "gbvrt": []}
    refseq_filelists = {"archaea": [], "bacteria": [], "fungi": [], "invertebrate": [], "plant": [], "protozoa": [], "vertebrate_mammalian": [], "vertebrate_other": [], "viral": []}
    progress_timer = time.time()

    print("Fetching http://ftp.ncbi.nlm.nih.gov/genbank/")
    f = urllib2.urlopen("http://ftp.ncbi.nlm.nih.gov/genbank/")
    soup = BeautifulSoup(f.read(), 'html.parser')
    for link in soup.find_all("a"): # all <a> tags
        line = link.get("href")
        if len(line) > 0:
            fl = line.split()[-1]
            if fl[0:5] in genbank_filelists.keys():
                genbank_filelists[fl[0:5]].append(fl)

    if (time.time()-progress_timer) >= 300:
        progress_timer = time.time()
        pyhive.proc.req_progress(99, 100)         
         
    for div in refseq_divisions:
        r = StringIO()

        print("Fetching http://ftp.ncbi.nlm.nih.gov/genomes/refseq/%s/assembly_summary.txt" % div)
        f = urllib2.urlopen("http://ftp.ncbi.nlm.nih.gov/genomes/refseq/%s/assembly_summary.txt" % div)
        r.write(f.read())

        for line in r.getvalue().split("\n")[2:]:
            if len(line) <= 1:
                continue
            s = line.split("\t")

            if s[10] != "latest":
                continue
            
            asm = s[0]
            taxid = s[5]
            name = s[7]
            path = s[19] + "/" + s[19].split("/")[-1] + "_genomic.gbff.gz"
            path = "ht" + path[1:] # replace the start (ftp) with http
            
            refseq_filelists[div].append("|".join([div,asm,taxid,name,path]))
            
            if (time.time()-progress_timer) >= 300:
                progress_timer = time.time()
                pyhive.proc.req_progress(99, 100)
                
    print "finished pulling lists"
            
    pyhive.proc.req_set_data("file://filelisting.txt", req = pyhive.proc.grp_id)
    outfile = pyhive.proc.req_get_data_path("filelisting.txt", req = pyhive.proc.grp_id) # retrieve path to file
    with open(outfile, "w") as outfh:
        for key in sorted(genbank_filelists.keys()):
            for entry in genbank_filelists[key]:
                outfh.write(entry + "\n")
                
        for key in sorted(refseq_filelists.keys()):
            for entry in refseq_filelists[key]:
                outfh.write(entry + "\n")

    print "finished writing lists"

                
def create_all_requests():
    start = 0
    index = 0
    cur_weight = 0
    progress_timer = time.time()
    rn = 1
    
    print "starting to create requests"
    
    infile = pyhive.proc.req_get_data_path("filelisting.txt", req = pyhive.proc.grp_id)
    with open(infile, "r") as infh:
        firstline = infh.next()
        if "|" in firstline:
            previous_div = firstline.split("|")[0]
            cur_weight += refseq_weights[previous_div]
        else:
            previous_div = firstline[0:5]
            cur_weight += genbank_weights[previous_div]

        index += 1
        
        for line in infh:
            if "|" in line:
                max_weight = 5000
                div = line.split("|")[0]
                weight = refseq_weights[div]
            else:
                max_weight = 5
                div = line[0:5]
                weight = genbank_weights[div]
                
            if (div != previous_div) and (cur_weight > 0):  # if you've reached the end of a division, flush it out to a new request [so each request can maintain a single division]
                create_request(previous_div, start, index, rn)  # not +1 because you're already past the last line
                rn += 1
                cur_weight = 0
                start = index  # not +1 because the new start is on the current line
                
            previous_div = div    
            cur_weight += weight
            if (cur_weight >= max_weight):
                create_request(div, start, index+1, rn)  # +1 because list is exclusive
                rn += 1
                cur_weight = 0
                start = index+1  # +1 because the start should be the next index
                
            index += 1
            
            if (time.time()-progress_timer) >= 300:
                progress_timer = time.time()
                pyhive.proc.req_progress(99, 100)
                
    if (cur_weight >= 0):  # if you reach the end of the file and there's still something left...
        create_request(div, start, index, rn)
        
    print "created all requests"
                
                
def create_request(division, start, end, rn):
    qpsvc = pyhive.QPSvc(pyhive.proc.svc.name)
    qpsvc.set_form(pyhive.proc.form)
    if division in genbank_divisions:
        qpsvc.set_var("data_source", "genbank")
    elif division in refseq_divisions:
        qpsvc.set_var("data_source", "refseq")
    else:
        return  # should never go here?
    qpsvc.set_var("division", division)
    qpsvc.set_var("start", str(start))
    qpsvc.set_var("end", str(end))
    req_id = qpsvc.launch()
                

def get_filelist():
    data_source = str(pyhive.proc.form["data_source"])
    division = str(pyhive.proc.form["division"])
    start_index = int(pyhive.proc.form["start"])
    end_index = int(pyhive.proc.form["end"])
    filelist = []
    index = 0
    
    
    infile = pyhive.proc.req_get_data_path("filelisting.txt", req = pyhive.proc.grp_id)
    print infile
    with open(infile, "r") as infh:
        for line in infh:
            if index >= end_index:
                break
            if index >= start_index:
                filelist.append(line.rstrip())
            index += 1
            
    print pyhive.proc.req_id, filelist
    return filelist        
    

def print_exception_source(assembly, accession, protein_id):
    exc_type, exc_obj, tb = sys.exc_info()
    lineno = tb.tb_lineno
    filename = tb.tb_frame.f_code.co_filename
    line = linecache.getline(filename, lineno).strip()

    return "\t".join([assembly, accession, protein_id, str(exc_type.__name__), str(exc_obj), line]) + "\n"


def get_file_directory():  # points to where the .genomic.gbff.gz or .seq.gz files are stored
    dir = pyhive.proc.config_get("refseq_processor.downloads") + "/"
    assert dir != "/"
    if not os.path.exists(dir):
        os.mkdir(dir)
    assert os.path.isdir(dir) and os.access(dir, os.W_OK)
    return dir


def refseq_check_file_downloads():
    refseq_filelist = get_filelist()
    file_directory = get_file_directory()
    progress_timer = time.time()

    '''connection_attempts = 0
    while connection_attempts < 5:
        try:
            ftp = ftplib.FTP("ftp.ncbi.nlm.nih.gov", "anonymous", "john.athey@fda.hhs.gov")
            break
        except:  # not sure exactly what the error is
            connection_attempts += 1
            if connection_attempts == 5:
                pyhive.proc.req_set_status(pyhive.req_status.PROG_ERROR("Failed to establish ftp connection to ftp.ncbi.nlm.nih.gov"))
                raise
            if (time.time()-progress_timer) >= 300:
                progress_timer = time.time()
                pyhive.proc.req_progress(1,100)
            time.sleep(30)'''

    #pattern = re.compile(r'(genomes/all/GCF_.*)')

    for line in refseq_filelist:
        url = line.split("|")[-1]

        '''match = pattern.search(url)
        try:
            ftp_path = match.group(0)  # e.g. 'genomes/all/GCF_000302455.1_ASM30245v1/GCF_000302455.1_ASM30245v1_genomic.gbff.gz'
        except AttributeError as e:
            print e
            pyhive.proc.req_set_status(pyhive.req_status.PROG_ERROR, "Failed URL:" + url)
            pyhive.proc.req_set_status(pyhive.req_status.PROG_ERROR, "Failed line:" + line)
            raise

        filename = ftp_path.split("/")[-1]  # e.g. 'GCF_000302455.1_ASM30245v1_genomic.gbff.gz'
        filepath = file_directory + filename'''

        download_attempts = 0
        
        filename = url.split("/")[-1]
        filepath = file_directory + filename
        
        try:
            pyhive.proc.req_lock(filepath)

            download_needed = True

            if os.path.exists(filepath):
                # check if file needs to be updated
                try:
                    head_request = urllib2.Request(url)
                    head_request.get_method = lambda : "HEAD"
                    head_response = urllib2.urlopen(head_request)
                    remote_size = int(head_response.headers["Content-Length"])
                    remote_mtime = time.mktime(email.utils.parsedate(head_response.headers["Last-Modified"]))
                    local_stat = os.stat(filepath)
                    if local_stat.st_size == remote_size and local_stat.st_mtime >= remote_mtime:
                        download_needed = False
                        print("%s was already downloaded" % filename)
                except:
                    print("HTTP HEAD for %s failed" % url)
                    raise

            while download_needed and download_attempts < 5:
                try:
                    print("Downloading %s to %s (attempt %s/5)" % (url, filepath, download_attempts + 1))
                    filewriter = open(filepath, "wb")
                    f = urllib2.urlopen(url)
                    filewriter.write(f.read())
                    filewriter.close()
                    if (time.time()-progress_timer) >= 300:
                        progress_timer = time.time()
                        pyhive.proc.req_progress(1,100)
                    break
                except:  # not sure exactly what the error is
                    download_attempts += 1
                    if download_attempts == 5:
                        pyhive.proc.req_set_info(pyhive.log_type.ERROR, "Failed to download file %s" % filename)
                        pyhive.proc.req_set_status(pyhive.req_status.PROG_ERROR)
                        raise
                    if (time.time()-progress_timer) >= 300:
                        progress_timer = time.time()
                        pyhive.proc.req_progress(1,100)
                    time.sleep(30)
                    
            pyhive.proc.req_unlock(filepath)

        except pyhive.AlreadyLockedError as e:
            print e

        '''try:
            pyhive.proc.req_lock(filepath)

            rm_time_ftp = ftp.sendcmd("MDTM %s" % ftp_path).split(" ")[1]  # returns string of modification date [of remote file], e.g. 20150903154006
            rm_time_str = " ".join(
                [str(rm_time_ftp[0:4]), str(rm_time_ftp[4:6]), str(rm_time_ftp[6:8]), str(rm_time_ftp[8:10]),
                 str(rm_time_ftp[10:12]),
                 str(rm_time_ftp[12:14])])  # format into readable string, e.g. 2015 09 03 15 40 06
            rm_time = time.strptime(rm_time_str, "%Y %m %d %H %M %S")  # create a time object

            if not os.path.exists(filepath):
                print "File %s not found, downloading now" % filename
                while download_attempts < 5:
                    try:
                        filewriter = open(filepath, "wb")
                        ftp.retrbinary('RETR %s' % ftp_path, filewriter.write)
                        filewriter.close()
                        if (time.time()-progress_timer) >= 300:
                            progress_timer = time.time()
                            pyhive.proc.req_progress(1,100)
                        break
                    except:  # not sure exactly what the error is
                        download_attempts += 1
                        if download_attempts == 5:
                            pyhive.proc.req_set_status(pyhive.req_status.PROG_ERROR("Failed to download file:" +filename))
                            raise
                        if (time.time()-progress_timer) >= 300:
                            progress_timer = time.time()
                            pyhive.proc.req_progress(1,100)
                        time.sleep(30)

            else:
                # may want to build in something to check whether the size is right #
                lm_time = time.gmtime(os.path.getmtime(filepath))

                if rm_time > lm_time:
                    print "Need to update %s, downloading now" % filename
                    while download_attempts < 5:
                        try:
                            filewriter = open(filepath, "wb")
                            ftp.retrbinary('RETR %s' % ftp_path, filewriter.write)
                            filewriter.close()
                            if (time.time()-progress_timer) >= 300:
                                progress_timer = time.time()
                                pyhive.proc.req_progress(1,100)
                            break
                        except:  # not sure exactly what the error is
                            download_attempts += 1
                            if download_attempts == 5:
                                pyhive.proc.req_set_status(pyhive.req_status.PROG_ERROR("Failed to download file:" +filename))
                                raise
                            if (time.time()-progress_timer) >= 300:
                                progress_timer = time.time()
                                pyhive.proc.req_progress(1,100)
                            time.sleep(30)

                else:
                    print "File %s is up to date" % filename
                    #pass

            pyhive.proc.req_unlock(filepath)

        except pyhive.AlreadyLockedError as e:
            print e'''

    return refseq_filelist


def genbank_check_file_downloads():
    genbank_filelist = get_filelist()
    file_directory = get_file_directory()
    progress_timer = time.time()

    '''with open(filelist_path, "r") as fh:
        for line in fh:
            #print "cur_line = %d, min_line = %d, max_line = %d, line = %s" % (cur_line, min_line, max_line, line)
            if cur_line >= max_line:
                break
            if cur_line >= min_line:
                genbank_filelist.append(line.rstrip())
            cur_line += 1'''


    '''connection_attempts = 0
    while connection_attempts < 5:
        try:
            ftp = ftplib.FTP("ftp.ncbi.nlm.nih.gov", "anonymous", "john.athey@fda.hhs.gov")
            break
        except:  # not sure exactly what the error is
            connection_attempts += 1
            if connection_attempts == 5:
                pyhive.proc.req_set_status(pyhive.req_status.PROG_ERROR("Failed to establish ftp connection to ftp.ncbi.nlm.nih.gov"))
                raise
            if (time.time()-progress_timer) >= 300:
                progress_timer = time.time()
                pyhive.proc.req_progress(1,100)
            time.sleep(30)'''


    for line in genbank_filelist:
        #ftp_path = "genbank/" + line.rstrip()
        #filename = line.rstrip()
        
        url = "http://ftp.ncbi.nlm.nih.gov/genbank/" + line.rstrip()
        filename = line.rstrip()
        filepath = file_directory + filename

        download_attempts = 0
        
        try:
            pyhive.proc.req_lock(filepath)
            
            while download_attempts < 5:
                try:
                    filewriter = open(filepath, "wb")
                    f = urllib2.urlopen(url)
                    filewriter.write(f.read())
                    filewriter.close()
                    if (time.time()-progress_timer) >= 300:
                        progress_timer = time.time()
                        pyhive.proc.req_progress(1,100)
                    break
                except:  # not sure exactly what the error is
                    download_attempts += 1
                    if download_attempts == 5:
                        pyhive.proc.req_set_status(pyhive.req_status.PROG_ERROR("Failed to download file:" +filename))
                        raise
                    if (time.time()-progress_timer) >= 300:
                        progress_timer = time.time()
                        pyhive.proc.req_progress(1,100)
                    time.sleep(30)
                    
            pyhive.proc.req_unlock(filepath)

        except pyhive.AlreadyLockedError as e:
            print e

        '''try:
            pyhive.proc.req_lock(filepath)

            rm_time_ftp = ftp.sendcmd("MDTM %s" % ftp_path).split(" ")[1]  # returns string of modification date [of remote file], e.g. 20150903154006
            rm_time_str = " ".join(
                [str(rm_time_ftp[0:4]), str(rm_time_ftp[4:6]), str(rm_time_ftp[6:8]), str(rm_time_ftp[8:10]),
                 str(rm_time_ftp[10:12]),
                 str(rm_time_ftp[12:14])])  # format into readable string, e.g. 2015 09 03 15 40 06
            rm_time = time.strptime(rm_time_str, "%Y %m %d %H %M %S")  # create a time object

            if not os.path.exists(filepath):
                print "File %s not found, downloading now" % filename
                while download_attempts < 5:
                    try:
                        filewriter = open(filepath, "wb")
                        ftp.retrbinary('RETR %s' % ftp_path, filewriter.write)
                        filewriter.close()
                        if (time.time()-progress_timer) >= 300:
                                progress_timer = time.time()
                                pyhive.proc.req_progress(1,100)
                        break
                    except:  # not sure exactly what the error is
                        download_attempts += 1
                        if download_attempts == 5:
                            pyhive.proc.req_set_status(pyhive.req_status.PROG_ERROR("Failed to download file:" +filename))
                            raise
                        if (time.time()-progress_timer) >= 300:
                                progress_timer = time.time()
                                pyhive.proc.req_progress(1,100)
                        time.sleep(30)

            else:
                # may want to build in something to check whether the size is right #
                lm_time = time.gmtime(os.path.getmtime(filepath))

                if rm_time > lm_time:
                    print "Need to update %s, downloading now" % filename
                    while download_attempts < 5:
                        try:
                            filewriter = open(filepath, "wb")
                            ftp.retrbinary('RETR %s' % ftp_path, filewriter.write)
                            filewriter.close()
                            if (time.time()-progress_timer) >= 300:
                                progress_timer = time.time()
                                pyhive.proc.req_progress(1,100)
                            break
                        except:  # not sure exactly what the error is
                            download_attempts += 1
                            if download_attempts == 5:
                                pyhive.proc.req_set_status(pyhive.req_status.PROG_ERROR("Failed to download file:" +filename))
                                raise
                            if (time.time()-progress_timer) >= 300:
                                progress_timer = time.time()
                                pyhive.proc.req_progress(1,100)
                            time.sleep(30)

                else:
                    print "File %s is up to date" % filename
                    #pass

            pyhive.proc.req_unlock(filepath)

        except pyhive.AlreadyLockedError as e:
            print e'''

    return genbank_filelist


class SpeciesCodons(object):
    def __init__(self, division, assembly, taxid, species, organelle):
        self.division = division  # e.g. bacteria
        self.assembly = assembly  # e.g. GCF_000008865.1
        self.taxid = taxid  # e.g. 386585
        self.species = species  # e.g. "Escherichia coli O157:H7 str. Sakai"
        self.organelle = organelle  
        self.codons = CodonsDict.copy()
        self.transl_table = []
        self.num_included = 0  # num of CDSs counted
        self.nuc = NuclDict.copy()
        self.nuc1 = NuclDict.copy()
        self.nuc2 = NuclDict.copy()
        self.nuc3 = NuclDict.copy()
        self.gc = 0
        self.gc1 = 0
        self.gc2 = 0
        self.gc3 = 0

    def calc_gc(self):
        for codon in self.codons.keys():
            self.nuc[codon[0]] += self.codons[codon]
            self.nuc1[codon[0]] += self.codons[codon]

            self.nuc[codon[1]] += self.codons[codon]
            self.nuc2[codon[1]] += self.codons[codon]

            self.nuc[codon[2]] += self.codons[codon]
            self.nuc3[codon[2]] += self.codons[codon]

        try:
            self.gc = float(self.nuc["G"] + self.nuc["C"])/sum(self.nuc.values())
            self.gc1 = float(self.nuc1["G"] + self.nuc1["C"])/sum(self.nuc1.values())
            self.gc2 = float(self.nuc2["G"] + self.nuc2["C"])/sum(self.nuc2.values())
            self.gc3 = float(self.nuc3["G"] + self.nuc3["C"])/sum(self.nuc3.values())
        except ZeroDivisionError as e:
            self.gc = 0
            self.gc1 = 0
            self.gc2 = 0
            self.gc3 = 0


    def format_output(self):
        if not self.transl_table:  # if the list is empty, it *should* be because GenBank format is to leave that tag out if the value is 1 (standard code)
            self.transl_table.append(1)
            
        out_string = "\t".join(
            [str(self.division), str(self.assembly), str(self.taxid), str(self.species), str(self.organelle),
             str(self.transl_table).strip('[]').replace('\'', ''), str(self.num_included),
             str(sum(self.codons.values())), str(round(self.gc*100,2)), str(round(self.gc1*100,2)), str(round(self.gc2*100,2)), str(round(self.gc3*100,2))])
        out_string = out_string + "\t"
        for codon in self.codons:
            out_string = out_string + str(self.codons[codon]) + "\t"
        out_string = out_string.rstrip() + "\n"
        return out_string


class CDS_Codons(object):
    def __init__(self, protein_id, accession, species, taxid, assembly, division, organelle):
        self.protein_id = protein_id
        self.accession = accession
        self.species = species
        self.taxid = taxid
        self.assembly = assembly
        self.division = division
        self.organelle = organelle
        self.codons = CodonsDict.copy()
        self.nuc = NuclDict.copy()
        self.nuc1 = NuclDict.copy()
        self.nuc2 = NuclDict.copy()
        self.nuc3 = NuclDict.copy()
        self.gc = 0
        self.gc1 = 0
        self.gc2 = 0
        self.gc3 = 0

    def calc_gc(self):
        for codon in self.codons.keys():
            self.nuc[codon[0]] += self.codons[codon]
            self.nuc1[codon[0]] += self.codons[codon]

            self.nuc[codon[1]] += self.codons[codon]
            self.nuc2[codon[1]] += self.codons[codon]

            self.nuc[codon[2]] += self.codons[codon]
            self.nuc3[codon[2]] += self.codons[codon]


        try:
            self.gc = float(self.nuc["G"] + self.nuc["C"])/sum(self.nuc.values())
            self.gc1 = float(self.nuc1["G"] + self.nuc1["C"])/sum(self.nuc1.values())
            self.gc2 = float(self.nuc2["G"] + self.nuc2["C"])/sum(self.nuc2.values())
            self.gc3 = float(self.nuc3["G"] + self.nuc3["C"])/sum(self.nuc3.values())

        except ZeroDivisionError as e:
            self.gc = 0
            self.gc1 = 0
            self.gc2 = 0
            self.gc3 = 0


    def format_output(self):
        out_string = "\t".join(
            [str(self.protein_id), str(self.accession), str(self.division), str(self.assembly), str(self.taxid),
             str(self.species), str(self.organelle), str(sum(self.codons.values())), str(round(self.gc*100,2)), str(round(self.gc1*100,2)),
             str(round(self.gc2*100,2)), str(round(self.gc3*100,2))])
        out_string = out_string + "\t"
        for codon in self.codons:
            out_string = out_string + str(self.codons[codon]) + "\t"
        out_string = out_string.rstrip() + "\n"
        return out_string


def refseq_check_total_CDS(refseq_filelist):
    progress_timer = time.time()
    total_num_CDS = 0

    for line in refseq_filelist:
        url = line.split("|")[-1]
        fl = get_file_directory() + url.split("/")[-1]

        bash_cmd = 'zgrep \"  CDS  \" %s | wc' % fl
        process = subprocess.check_output(bash_cmd, shell = True)
        total_num_CDS += int(process.strip().split()[0])

        if (time.time()-progress_timer) >= 300:
            progress_timer = time.time()
            pyhive.proc.req_progress(1,100)

    return total_num_CDS


def genbank_check_total_CDS(genbank_filelist):
    progress_timer = time.time()
    total_num_CDS = 0

    for line in genbank_filelist:
        fl = get_file_directory() + line.rstrip()

        bash_cmd = 'zgrep \"  CDS  \" %s | wc' % fl
        process = subprocess.check_output(bash_cmd, shell = True)
        total_num_CDS += int(process.strip().split()[0])

        if (time.time()-progress_timer) >= 300:
            progress_timer = time.time()
            pyhive.proc.req_progress(1,100)

    print "Total CDS:", total_num_CDS
    return total_num_CDS


def refseq_execute():
    start_time = time.time()
    species_counts = {}  # key is assembly ID (e.g. GCF_000302455.1), value is SpeciesCodons object

    pyhive.proc.req_progress(1, 100)  # just in case the timer never triggers within the function
    refseq_filelist = refseq_check_file_downloads()
    pyhive.proc.req_progress(1, 100)  # just in case the timer never triggers within the function
    total_num_CDS = refseq_check_total_CDS(refseq_filelist)
    pyhive.proc.req_progress(1, 100)  # just in case the timer never triggers within the function
    num_CDS_finished = 0

    ### Create refseq_CDS.tsv file for writing, with headers ###
    pyhive.proc.req_set_data("file://refseq_CDS_individual.tsv")  # create refseq_CDS.tsv in file-based blob storage for current request
    CDS_outfile = pyhive.proc.req_get_data_path("refseq_CDS_individual.tsv") # retrieve path to CDS.tsv belonging to current request
    CDS_outfh = open(CDS_outfile, "w")
    headers = "Protein ID" + "\t" + "Accession" + "\t" + "Division" + "\t" + "Assembly" + "\t" + "Taxid" + "\t" + "Species" + "\t" + "Organelle" + "\t" + "# Codons" + "\t" + "GC%" + "\t" + "GC1%" + "\t" + "GC2%" + "\t" + "GC3%" + "\t"
    for codon in CodonsDict.keys():
        headers = headers + codon + "\t"
    headers = headers.rstrip() + "\n"
    CDS_outfh.write(headers)

    ### Create refseq_errors.tsv file for writing, with headers ###
    pyhive.proc.req_set_data("file://refseq_errors_individual.tsv")  # create errors.tsv in file-based blob storage for current request
    error_outfile = pyhive.proc.req_get_data_path("refseq_errors_individual.tsv")  # retrieve path to errors.tsv belonging to current request
    error_outfh = open(error_outfile, "w")
    error_outfh.write("Assembly" + "\t" + "Accession" + "\t" + "Protein ID" + "\t" + "ErrorType" + "\t" + "Error Text" + "\t" + "Source Line" + "\n")

    progress_timer = time.time()

    for line in refseq_filelist:
        splitline = line.split("|")
        #division = splitline[0]  # e.g. "bacteria"
        division = "refseq"  # for new output data format(?)
        assembly = splitline[1]  # e.g. "GCF_000008865.1"
        real_assembly = splitline[1]
        taxid = splitline[2]  # e.g. 386585
        species = splitline[3]
        url = splitline[4]  # e.g. ftp://ftp.ncbi.nlm.nih.gov/genomes/all/GCF_000008865.1_ASM886v1

        fl = get_file_directory() + url.split("/")[-1]  # should be something like "./files/" + "GCF_000302455.1_ASM30245v1_genomic.gbff.gz"
        print "Working with " + fl

        infh = gzip.open(fl, 'rb')  # open the .gz file for reading

        for seq_record in SeqIO.parse(infh, "genbank"):  # parse through each record in the file
            ###########################################################################################################
            ### This parses out the species name, including mitochondrial, while getting rid of common names    ###
            ### Handles all the cases I'm aware of, including:                            ###
            ###     Homo sapiens (human) -> Homo sapiens                                ###
            ###     mitochondrion Capra hircus (goat) -> mitochondrion Capra hircus                    ###
            ###    Escherichia coli -> Escherichia coli                                ###
            ###     Xenopus (Silurana) tropicalis (western clawed frog) -> Xenopus (Silurana) tropicalis        ###
            ###########################################################################################################

            a, sep, b = seq_record.annotations["source"].rpartition('(')
            species_from_file = a or b
            organelle = "genomic"

            # need to separate out mitochondrial/chloroplastic genomes from the main genome #
            assembly = splitline[1] # resetting in case the mitochondrion isn't the last record in the file
            if "mitochondrion" in species_from_file:
                organelle = "mitochondrion"
                assembly = assembly + "_mitochondrion"
            elif "chloroplast" in species_from_file:
                organelle = "plastid"
                assembly = assembly + "_plastid"
            elif "plastid" in species_from_file:
                organelle = "plastid"
                assembly = assembly + "_plastid"
            elif "chromoplast" in species_from_file:
                organelle = "plastid"
                assembly = assembly + "_plastid"
            elif "leucoplast" in species_from_file:
                organelle = "plastid"
                assembly = assembly + "_plastid"
            else:
                organelle = "genomic"

            for feat in seq_record.features:  # parse through each feature
                if (feat.type == "CDS") and ("pseudo" not in feat.qualifiers.keys()) and ("pseudogene" not in feat.qualifiers.keys()) and ("LOW QUALITY" not in seq_record.description):  # ignore pseudogenes and "low quality" genes with base-correction [may get parsed incorrectly]
                    
                    try:
                        if "LOW QUALITY" in feat.qualifiers["product"][0]:
                            continue  # another check to skip low quality proteins; checking the seq_record.description probably only works in GenBank
                    except (KeyError, IndexError) as e:
                        pass
                    
                    
                    if assembly not in species_counts.keys():  # create a new instance of SpeciesCodons if it doesn't exist for that species yet
                        species_counts[assembly] = SpeciesCodons(division, real_assembly, taxid, species, organelle)


                    ###################################################################################################
                    ### It probably isn't the smartest to wrap this whole thing in a try/except,             ###
                    ###     but Genbank is formatted so strangely/inconsistently sometimes that it was very hard    ###
                    ###    to predict or account for all the weird errors I got.                    ###
                    ### The most problematic lines I remember were the first 4 in the try, which            ###
                    ###     usually just means the file wasn't annotated fully/properly, or                ###
                    ###    that Biopython failed to extract the sequence properly, which usually            ###
                    ###    happens when the actual sequence data is just referenced elsewhere            ###
                    ###    (e.g. a CDS will say XM_12345.1 1..300, not its own data)                ###
                    ###################################################################################################

                    try:
                        try:
                            accession = seq_record.annotations["accessions"][0]  # not sure if there's ever more than 1?
                        except KeyError:
                            accession = "undefined"

                        try:
                            protein_id = feat.qualifiers["protein_id"][0]
                        except KeyError:
                            protein_id = "undefined"

                        codon_start = int(feat.qualifiers["codon_start"][0]) - 1  # -1 for zero-based index

                        cds = CDS_Codons(protein_id, accession, species, taxid, assembly, division, organelle)  # instance of CDS_codons class, only one at a time

                        if "transl_table" in feat.qualifiers:
                            if feat.qualifiers["transl_table"][0] not in species_counts[assembly].transl_table:
                                species_counts[assembly].transl_table.append(feat.qualifiers["transl_table"][0])

                        len_sequence = 0
                        seq_codon_fragment = None

                        for loc in feat.location.parts:

                            loc_start = loc.nofuzzy_start
                            loc_end = loc.nofuzzy_end
                            #print "loc_start", loc_start, "loc_end", loc_end
                            loc_seq = seq_record.seq[loc_start:loc_end]

                            #if loc.strand == -1: # might need to switch this back??
                            if feat.strand == -1:
                                if isinstance(loc_seq, MutableSeq):
                                    loc_seq = loc_seq.toseq()
                                try:
                                    loc_seq = loc_seq.reverse_complement()
                                except AttributeError:
                                    loc_seq = reverse_complement(loc_seq)

                            if seq_codon_fragment:
                                codon = seq_codon_fragment + str(loc_seq[codon_start: 3 - len(seq_codon_fragment)])
                                if codon in species_counts[assembly].codons:
                                    species_counts[assembly].codons[codon] += 1
                                    cds.codons[codon] += 1
                                codon_start = 3 - len(seq_codon_fragment)
                                seq_codon_fragment = None


                            for i in range(codon_start, len(loc_seq), 3):
                                if i + 3 > len(loc_seq):
                                    seq_codon_fragment = str(loc_seq[i: len(loc_seq)])
                                    break

                                codon = str(loc_seq[i:i + 3])

                                if codon in species_counts[assembly].codons:
                                    species_counts[assembly].codons[codon] += 1
                                    cds.codons[codon] += 1
                                else:
                                    pass  # no ambiguous nucleotides
                            #print "\n"

                            len_sequence += loc_end - codon_start - loc_start
                            codon_start = 0

                        cds.calc_gc()


                        species_counts[assembly].num_included += 1  # counts the # of CDSs included
                        #print "species count updated"


                        out_string = cds.format_output()
                        CDS_outfh.write(out_string)


                    except (ValueError, KeyError):
                        if "accessions" in seq_record.annotations:
                            accession = seq_record.annotations["accessions"][0]
                        else:
                            accession = "undef"

                        if "protein_id" in feat.qualifiers:
                            protein_id = feat.qualifiers["protein_id"][0]
                        else:
                            protein_id = "undef"

                        print print_exception_source(assembly, accession, protein_id)
                        error_outfh.write(print_exception_source(assembly, accession, protein_id))


                    num_CDS_finished += 1
                    if num_CDS_finished%1000 == 0:
                        progress_timer = time.time()
                        pyhive.proc.req_progress(num_CDS_finished, total_num_CDS)

                    elif (time.time() - progress_timer) >= 300:
                        progress_timer = time.time()
                        pyhive.proc.req_progress(num_CDS_finished, total_num_CDS)

                if (time.time() - progress_timer) >= 300:
                    progress_timer = time.time()
                    pyhive.proc.req_progress(num_CDS_finished, total_num_CDS)



        print "Finished with", fl.split("/")[-1], "at", time.ctime()  # just for info purposes
        infh.close()  # close the .gz file

    CDS_outfh.close()  # once all files are done, close the CDS file [it will be huge]
    error_outfh.close()

    for key in species_counts.keys():
        species_counts[key].calc_gc()


    pyhive.proc.req_set_data("file://refseq_species_individual.tsv") # create species.tsv in file-based blob storage for current request
    species_outfh = open(pyhive.proc.req_get_data_path("refseq_species_individual.tsv"), "w")
    headers = "Division" + "\t" + "Assembly" + "\t" + "Taxid" + "\t" + "Species" + "\t" + "Organelle" + "\t" + "Translation Table" + "\t" + "# CDS" + "\t" + "# Codons" + "\t" + "GC%" + "\t" + "GC1%" + "\t" + "GC2%" + "\t" + "GC3%" + "\t"
    for codon in CodonsDict.keys():
        headers = headers + codon + "\t"
    headers = headers.rstrip() + "\n"
    species_outfh.write(headers)

    for key in species_counts.keys():
        out_string = species_counts[key].format_output()
        species_outfh.write(out_string)
        if (time.time() - progress_timer) >= 300:
            progress_timer = time.time()
            pyhive.proc.req_progress(num_CDS_finished, total_num_CDS)

    species_outfh.close()
    print "Minutes elapsed:", (time.time() - start_time) / 60
    
def genbank_execute():
    start_time = time.time()
    species_counts = {}  # key is species name, value is SpeciesCodons object

    pyhive.proc.req_progress(1, 100)  # just in case the timer never triggers within the function
    genbank_filelist = genbank_check_file_downloads()
    pyhive.proc.req_progress(1, 100)  # just in case the timer never triggers within the function
    total_num_CDS = genbank_check_total_CDS(genbank_filelist)
    num_CDS_finished = 0

    ### Create genbank_CDS.tsv file for writing, with headers ###
    pyhive.proc.req_set_data("file://genbank_CDS_individual.tsv")  # create genbank_CDS.tsv in file-based blob storage for current request
    CDS_outfile = pyhive.proc.req_get_data_path("genbank_CDS_individual.tsv") # retrieve path to CDS.tsv belonging to current request
    CDS_outfh = open(CDS_outfile, "w")
    headers = "Protein ID" + "\t" + "Accession" + "\t" + "Division" + "\t" + "Assembly" + "\t" + "Taxid" + "\t" + "Species" + "\t" + "Organelle" + "\t" + "# Codons" + "\t" + "GC%" + "\t" + "GC1%" + "\t" + "GC2%" + "\t" + "GC3%" + "\t"
    for codon in CodonsDict.keys():
        headers = headers + codon + "\t"
    headers = headers.rstrip() + "\n"
    CDS_outfh.write(headers)

    ### Create genbank_errors.tsv file for writing, with headers ###
    pyhive.proc.req_set_data("file://genbank_errors_individual.tsv")  # create errors.tsv in file-based blob storage for current request
    error_outfile = pyhive.proc.req_get_data_path("genbank_errors_individual.tsv")  # retrieve path to errors.tsv belonging to current request
    error_outfh = open(error_outfile, "w")
    error_outfh.write("Assembly" + "\t" + "Accession" + "\t" + "Protein ID" + "\t" + "ErrorType" + "\t" + "Error Text" + "\t" + "Source Line" + "\n")

    progress_timer = time.time()

    assembly = "NA"  # not applicable to genbank
    division = "genbank"


    for line in genbank_filelist:
        fl = get_file_directory() + line.rstrip()  # should be something like "./files/" + "gbbct1.seq.gz"
        print "Working with " + fl

        infh = gzip.open(fl, 'rb')  # open the .gz file for reading

        for seq_record in SeqIO.parse(infh, "genbank"):  # parse through each record in the file
            ###########################################################################################################
            ### This parses out the species name, including mitochondrial, while getting rid of common names    ###
            ### Handles all the cases I'm aware of, including:                            ###
            ###     Homo sapiens (human) -> Homo sapiens                                ###
            ###     mitochondrion Capra hircus (goat) -> mitochondrion Capra hircus                    ###
            ###    Escherichia coli -> Escherichia coli                                ###
            ###     Xenopus (Silurana) tropicalis (western clawed frog) -> Xenopus (Silurana) tropicalis        ###
            ###########################################################################################################

            a, sep, b = seq_record.annotations["source"].rpartition('(')
            species = a or b
            organelle = "genomic"

            # need to separate out mitochondrial/chloroplastic genomes from the main genome #
            if "mitochondrion" in species:
                real_species = " ".join(species.split(" ")[1:])  # cut the organelle name out of the species name
                organelle = "mitochondrion"
            elif "chloroplast" in species:
                real_species = " ".join(species.split(" ")[1:])  # cut the organelle name out of the species name
                organelle = "plastid"
            elif "plastid" in species:
                real_species = " ".join(species.split(" ")[1:])  # cut the organelle name out of the species name
                organelle = "plastid"
            elif "chromoplast" in species:
                real_species = " ".join(species.split(" ")[1:])  # cut the organelle name out of the species name
                organelle = "plastid"
            elif "leucoplast" in species:
                real_species = " ".join(species.split(" ")[1:])  # cut the organelle name out of the species name
                organelle = "plastid"
            else:
                real_species = species
                organelle = "genomic"

            taxid = 0  # not known in advance -- 0 is a dummy value

            for feat in seq_record.features:  # parse through each feature
                if (feat.type == "source"):
                    try:
                        xref_list = feat.qualifiers["db_xref"]
                        for xref in xref_list:
                            s = xref.split(":")
                            if s[0] == "taxon":
                                taxid = int(s[1])
                                break
                    except (KeyError, IndexError) as e:
                        pass  # no taxon found

                if (feat.type == "CDS") and ("pseudo" not in feat.qualifiers.keys()) and ("pseudogene" not in feat.qualifiers.keys()) and ("LOW QUALITY" not in seq_record.description):  # ignore pseudogenes and "low quality" genes with base-correction [may get parsed incorrectly]
                    
                    try:
                        if "LOW QUALITY" in feat.qualifiers["product"][0]:
                            continue  # another check to skip low quality proteins; checking the seq_record.description probably only works in GenBank
                    except (KeyError, IndexError) as e:
                        pass
                    
                    if species not in species_counts.keys():  # create a new instance of SpeciesCodons if it doesn't exist for that species yet
                        ### Don't use real_species here-- it will mess up the combine step because it's looking for the name with the organelle ###
                        #species_counts[species] = SpeciesCodons(division, assembly, taxid, real_species, organelle)
                        species_counts[species] = SpeciesCodons(division, assembly, taxid, species, organelle)


                    ###################################################################################################
                    ### It probably isn't the smartest to wrap this whole thing in a try/except,             ###
                    ###     but Genbank is formatted so strangely/inconsistently sometimes that it was very hard    ###
                    ###    to predict or account for all the weird errors I got.                    ###
                    ### The most problematic lines I remember were the first 4 in the try, which            ###
                    ###     usually just means the file wasn't annotated fully/properly, or                ###
                    ###    that Biopython failed to extract the sequence properly, which usually            ###
                    ###    happens when the actual sequence data is just referenced elsewhere            ###
                    ###    (e.g. a CDS will say XM_12345.1 1..300, not its own data)                ###
                    ###################################################################################################

                    try:
                        try:
                            accession = seq_record.annotations["accessions"][0]  # not sure if there's ever more than 1?
                        except KeyError:
                            accession = "undefined"

                        try:
                            protein_id = feat.qualifiers["protein_id"][0]
                        except KeyError:
                            protein_id = "undefined"

                        codon_start = int(feat.qualifiers["codon_start"][0]) - 1  # -1 for zero-based index

                        cds = CDS_Codons(protein_id, accession, real_species, taxid, assembly, division, organelle)  # instance of CDS_codons class, only one at a time

                        if "transl_table" in feat.qualifiers:
                            if feat.qualifiers["transl_table"][0] not in species_counts[species].transl_table:
                                species_counts[species].transl_table.append(feat.qualifiers["transl_table"][0])

                        len_sequence = 0
                        seq_codon_fragment = None

                        for loc in feat.location.parts:

                            loc_start = loc.nofuzzy_start
                            loc_end = loc.nofuzzy_end
                            #print "loc_start", loc_start, "loc_end", loc_end
                            loc_seq = seq_record.seq[loc_start:loc_end]

                            #if loc.strand == -1: # might need to switch this back??
                            if feat.strand == -1:
                                if isinstance(loc_seq, MutableSeq):
                                    loc_seq = loc_seq.toseq()
                                try:
                                    loc_seq = loc_seq.reverse_complement()
                                except AttributeError:
                                    loc_seq = reverse_complement(loc_seq)

                            if seq_codon_fragment:
                                codon = seq_codon_fragment + str(loc_seq[codon_start: 3 - len(seq_codon_fragment)])
                                if codon in species_counts[species].codons:
                                    species_counts[species].codons[codon] += 1
                                    cds.codons[codon] += 1
                                codon_start = 3 - len(seq_codon_fragment)
                                seq_codon_fragment = None


                            for i in range(codon_start, len(loc_seq), 3):
                                if i + 3 > len(loc_seq):
                                    seq_codon_fragment = str(loc_seq[i: len(loc_seq)])
                                    break

                                codon = str(loc_seq[i:i + 3])

                                if codon in species_counts[species].codons:
                                    species_counts[species].codons[codon] += 1
                                    cds.codons[codon] += 1
                                else:
                                    pass  # no ambiguous nucleotides
                            #print "\n"

                            len_sequence += loc_end - codon_start - loc_start
                            codon_start = 0

                        cds.calc_gc()


                        species_counts[species].num_included += 1  # counts the # of CDSs included


                        out_string = cds.format_output()
                        CDS_outfh.write(out_string)


                    except (ValueError, KeyError):
                        if "accessions" in seq_record.annotations:
                            accession = seq_record.annotations["accessions"][0]
                        else:
                            accession = "undef"

                        if "protein_id" in feat.qualifiers:
                            protein_id = feat.qualifiers["protein_id"][0]
                        else:
                            protein_id = "undef"

                        error_outfh.write(print_exception_source(fl, accession, protein_id))


                    num_CDS_finished += 1
                    if num_CDS_finished%1000 == 0:
                        progress_timer = time.time()
                        pyhive.proc.req_progress(num_CDS_finished, total_num_CDS)

                    elif (time.time() - progress_timer) >= 300:
                        progress_timer = time.time()
                        pyhive.proc.req_progress(num_CDS_finished, total_num_CDS)

                if (time.time() - progress_timer) >= 300:
                    progress_timer = time.time()
                    pyhive.proc.req_progress(num_CDS_finished, total_num_CDS)



        print "Finished with", fl, "at", time.ctime()  # just for info purposes
        infh.close()  # close the .gz file

    CDS_outfh.close()  # once all files are done, close the CDS file [it will be huge]
    error_outfh.close()

    #for key in species_counts.keys():  # no point for genbank now-- will be calculated later when files are combined
    #    species_counts[key].calc_gc()


    pyhive.proc.req_set_data("file://genbank_species_individual.tsv") # Note -- this is an intermediary, since the file's entries still need to be joined if the same species is in another file as well
    species_outfh = open(pyhive.proc.req_get_data_path("genbank_species_individual.tsv"), "w")
    headers = "Division" + "\t" + "Assembly" + "\t" + "Taxid" + "\t" + "Species" + "\t" + "Organelle" + "\t" + "Translation Table" + "\t" + "# CDS" + "\t" + "# Codons" + "\t" + "GC%" + "\t" + "GC1%" + "\t" + "GC2%" + "\t" + "GC3%" + "\t"
    for codon in CodonsDict.keys():
        headers = headers + codon + "\t"
    headers = headers.rstrip() + "\n"
    species_outfh.write(headers)

    for key in species_counts.keys():
        out_string = species_counts[key].format_output()
        species_outfh.write(out_string)
        if (time.time()-progress_timer) >= 300:
            progress_timer = time.time()
            pyhive.proc.req_progress(99, 100)

    species_outfh.close()
    print "Minutes elapsed:", (time.time() - start_time) / 60    

def get_req_data_source(req):
    try:
        return str(pyhive.proc.req_get_data("data_source", req = req))
    except SystemError:
        # SystemError: Failed to retrieve data blob from HIVE request
        return None

def combine_individual_outputs():
    progress_timer = time.time()
    

    # Combine RefSeq files #
    CDS_outfile = pyhive.proc.obj.add_file_path("refseq_CDS.tsv", True)
    print("Writing %s" % CDS_outfile)
    with open(CDS_outfile, "w") as CDS_outfh:
        headers = "Protein ID" + "\t" + "Accession" + "\t" + "Division" + "\t" + "Assembly" + "\t" + "Taxid" + "\t" + "Species" + "\t" + "Organelle" + "\t" + "# Codons" + "\t" + "GC%" + "\t" + "GC1%" + "\t" + "GC2%" + "\t" + "GC3%" + "\t"
        for codon in CodonsDict.keys():
            headers = headers + codon + "\t"
        headers = headers.rstrip() + "\n"
        CDS_outfh.write(headers)
        for req in pyhive.proc.grp2req():
            if get_req_data_source(req) == "refseq":
                CDS_infile = pyhive.proc.req_get_data_path("refseq_CDS_individual.tsv", req=req)
                with open(CDS_infile, "r") as CDS_infh:
                    CDS_infh.readline() # skip header line
                    for CDS_line in CDS_infh:
                        CDS_outfh.write(CDS_line)
                        if (time.time()-progress_timer) >= 300:
                            progress_timer = time.time()
                            pyhive.proc.req_progress(99, 100)


    species_outfile = pyhive.proc.obj.add_file_path("refseq_species.tsv", True)
    print("Writing %s" % species_outfile)
    with open(species_outfile, "w") as species_outfh:
        headers = "Division" + "\t" + "Assembly" + "\t" + "Taxid" + "\t" + "Species" + "\t" + "Organelle" + "\t" + "Translation Table" + "\t" + "# CDS" + "\t" + "# Codons" + "\t" + "GC%" + "\t" + "GC1%" + "\t" + "GC2%" + "\t" + "GC3%" + "\t"
        for codon in CodonsDict.keys():
            headers = headers + codon + "\t"
        headers = headers.rstrip() + "\n"
        species_outfh.write(headers)
        for req in pyhive.proc.grp2req():
            if get_req_data_source(req) == "refseq":
                species_infile = pyhive.proc.req_get_data_path("refseq_species_individual.tsv", req = req)
                with open(species_infile, "r") as species_infh:
                    species_infh.readline() # skip header line
                    for species_line in species_infh:
                        species_outfh.write(species_line)
                        if (time.time()-progress_timer) >= 300:
                            progress_timer = time.time()
                            pyhive.proc.req_progress(99, 100)


    '''error_outfile = pyhive.proc.obj.add_file_path("refseq_errors.tsv", True)
    with open(error_outfile, "w") as error_outfh:
        error_outfh.write("Assembly" + "\t" + "Accession" + "\t" + "Protein ID" + "\t" + "ErrorType" + "\t" + "Error Text" + "\t" + "Source Line" + "\n")
        for req in pyhive.proc.grp2req():
            if get_req_data_source(req) == "refseq":
                error_infile = pyhive.proc.req_get_data_path("refseq_errors_individual.tsv", req = req)
                with open(error_infile, "r") as error_infh:
                    error_infh.readline()  # skip header line
                    for error_line in error_infh:
                        error_outfh.wrote(error_line)
                        if (time.time()-progress_timer) >= 300:
                            progress_timer = time.time()
                            pyhive.proc.req_progress(99, 100)'''
                            
                            
                            
                            
    # Combine GenBank #                        
    pyhive.proc.req_progress(99, 100)
    codon_number = {}
    progress_timer = time.time()
    for i in range(0, len(CodonsDict.keys())):
        codon_number[i] = CodonsDict.keys()[i]
        
    species_outfile = pyhive.proc.obj.add_file_path("genbank_species.tsv", True)
    print("Writing %s" % species_outfile)
    with open(species_outfile, "w") as species_outfh:
        headers = "Division" + "\t" + "Assembly" + "\t" + "Taxid" + "\t" + "Species" + "\t" + "Organelle" + "\t" + "Translation Table" + "\t" + "# CDS" + "\t" + "# Codons" + "\t" + "GC%" + "\t" + "GC1%" + "\t" + "GC2%" + "\t" + "GC3%" + "\t"
        for codon in CodonsDict.keys():
            headers = headers + codon + "\t"
        headers = headers.rstrip() + "\n"
        species_outfh.write(headers)
        
        for div in genbank_divisions:  # do each GenBank division separately, to stop the dictionary from being massive
            combined_species = {}
            for req in pyhive.proc.grp2req():
                if get_req_data_source(req) == "genbank" and (str(pyhive.proc.req_get_data("division", req = req)) == div):
                    species_infile = pyhive.proc.req_get_data_path("genbank_species_individual.tsv", req = req)
                    with open(species_infile, "r") as species_infh:
                        species_infh.readline()  # skip header line
                        for line in species_infh:
                            splitline = line.split("\t")
                            #species = splitline[4]  # should be incorrect once headers are aligned correctly 
                            species = splitline[3]

                            if species not in combined_species.keys():
                                division = splitline[0]
                                assembly = splitline[1]
                                taxid = int(splitline[2])
                                #organelle = splitline[5]  # should be incorrect once headers are aligned correctly 
                                organelle = splitline[4]
                                
                                if "mitochondrion" in species:
                                    real_species = " ".join(species.split(" ")[1:])  # cut the organelle name out of the species name
                                    organelle = "mitochondrion"
                                elif "chloroplast" in species:
                                    real_species = " ".join(species.split(" ")[1:])  # cut the organelle name out of the species name
                                    organelle = "plastid"
                                elif "plastid" in species:
                                    real_species = " ".join(species.split(" ")[1:])  # cut the organelle name out of the species name
                                    organelle = "plastid"
                                elif "chromoplast" in species:
                                    real_species = " ".join(species.split(" ")[1:])  # cut the organelle name out of the species name
                                    organelle = "plastid"
                                elif "leucoplast" in species:
                                    real_species = " ".join(species.split(" ")[1:])  # cut the organelle name out of the species name
                                    organelle = "plastid"
                                else:
                                    real_species = species
                                    organelle = "genomic"

                                combined_species[species] = SpeciesCodons(division, assembly, taxid, real_species, organelle)

                                for i in range(0, len(CodonsDict.keys())):
                                    #combined_species[species].codons[codon_number[i]] = int(splitline[i+13]) # should be incorrect once headers are aligned correctly 
                                    combined_species[species].codons[codon_number[i]] = int(splitline[i+12])

                                #combined_species[species].num_included = int(splitline[7]) # should be incorrect once headers are aligned correctly 
                                combined_species[species].num_included = int(splitline[6])

                                #if splitline[6] != "":  # should be incorrect once headers are aligned correctly 
                                    #for translation_table_value in splitline[6].split(","): # should be incorrect once headers are aligned correctly 
                                        #combined_species[species].transl_table.append(int(translation_table_value.strip()))        
                                if splitline[5] != "":  
                                    for translation_table_value in splitline[5].split(","): 
                                        combined_species[species].transl_table.append(int(translation_table_value.strip()))                                        

                            else:
                                #combined_species[species].num_included += int(splitline[7])  # should be incorrect once headers are aligned correctly 
                                combined_species[species].num_included += int(splitline[6])
                                
                                #if splitline[6] != "":  # should be incorrect once headers are aligned correctly 
                                    #for translation_table_value in splitline[6].split(","):  # should be incorrect once headers are aligned correctly 
                                        #if int(translation_table_value.strip()) not in combined_species[species].transl_table:
                                            #combined_species[species].transl_table.append(int(translation_table_value))
                                if splitline[5] != "":  
                                    for translation_table_value in splitline[5].split(","):  
                                        if int(translation_table_value.strip()) not in combined_species[species].transl_table:
                                            combined_species[species].transl_table.append(int(translation_table_value))                                            

                                for i in range(0, len(CodonsDict.keys())):
                                    #combined_species[species].codons[codon_number[i]] += int(splitline[i+13])  # should be incorrect once headers are aligned correctly 
                                    combined_species[species].codons[codon_number[i]] += int(splitline[i+12])

                            if (time.time()-progress_timer) >= 300:
                                progress_timer = time.time()
                                pyhive.proc.req_progress(99, 100)

            for key in combined_species.keys():
                combined_species[key].calc_gc()
                if (time.time()-progress_timer) >= 300:
                    progress_timer = time.time()
                    pyhive.proc.req_progress(99, 100)


        
            progress_timer = time.time()


            for key in combined_species.keys():
                out_string = combined_species[key].format_output()
                species_outfh.write(out_string)
                if (time.time()-progress_timer) >= 300:
                    progress_timer = time.time()
                    pyhive.proc.req_progress(99, 100)                        

                    
    CDS_outfile = pyhive.proc.obj.add_file_path("genbank_CDS.tsv", True)
    print("Writing %s" % CDS_outfile)
    with open(CDS_outfile, "w") as CDS_outfh:
        headers = "Protein ID" + "\t" + "Accession" + "\t" + "Division" + "\t" + "Assembly" + "\t" + "Taxid" + "\t" + "Species" + "\t" + "Organelle" + "\t" + "# Codons" + "\t" + "GC%" + "\t" + "GC1%" + "\t" + "GC2%" + "\t" + "GC3%" + "\t"
        for codon in CodonsDict.keys():
            headers = headers + codon + "\t"
        headers = headers.rstrip() + "\n"
        CDS_outfh.write(headers)
        for req in pyhive.proc.grp2req():
            if get_req_data_source(req) == "genbank":
                CDS_infile = pyhive.proc.req_get_data_path("genbank_CDS_individual.tsv", req=req)
                with open(CDS_infile, "r") as CDS_infh:
                    CDS_infh.readline() # skip header line
                    for CDS_line in CDS_infh:
                        CDS_outfh.write(CDS_line)
                        if (time.time()-progress_timer) >= 300:
                            progress_timer = time.time()
                            pyhive.proc.req_progress(99, 100)
                            

                            
    db_outfile = pyhive.proc.obj.add_file_path("main_codon_columns.csv", True)
    print("Writing %s" % db_outfile)
    db_outfh = open(db_outfile, "w")
    gb_infh = open(pyhive.proc.obj.get_file_path("genbank_species.tsv"), "r")
    gb_infh.next()  # skip header line
    rs_infh = open(pyhive.proc.obj.get_file_path("refseq_species.tsv"), "r")
    rs_infh.next()  # skip header line

    db_outfh.write("Division,Assembly,Taxid,Species,Organelle\n")
    #db_outfh.write("division,assembly,taxid,name,type\n")
    
    for line in gb_infh:
        line = line.rstrip()
        s = line.split("\t")
        
        div = s[0]
        asm = s[1]
        taxid = s[2]
        
        #if "," in s[4]:  # should be incorrect once headers are aligned correctly 
        #    name = '\"' + s[4] + '\"'  # should be incorrect once headers are aligned correctly 
        #else:  # should be incorrect once headers are aligned correctly 
        #    name = s[4]  # should be incorrect once headers are aligned correctly 
            
        if "," in s[3]:  
            name = '\"' + s[3] + '\"'
        else:
            name = s[3]        
        
        #type = s[5]  # should be incorrect once headers are aligned correctly 
        type = s[4]
        db_outfh.write(",".join([div,asm,str(taxid),name,type]) + "\n")
        
    for line in rs_infh:
        line = line.rstrip()
        s = line.split("\t")
        
        div = s[0]
        asm = s[1]
        taxid = s[2]
        
        #if "," in s[4]:  # should be incorrect once headers are aligned correctly 
        #    name = '\"' + s[4] + '\"'  # should be incorrect once headers are aligned correctly 
        #else:  # should be incorrect once headers are aligned correctly 
        #    name = s[4]  # should be incorrect once headers are aligned correctly 
            
        if "," in s[3]:  
            name = '\"' + s[3] + '\"'
        else:
            name = s[3] 
        
        #type = s[5]  # should be incorrect once headers are aligned correctly 
        type = s[4]
        db_outfh.write(",".join([div,asm,str(taxid),name,type]) + "\n")
        
    db_outfh.close()
    gb_infh.close()
    rs_infh.close()

    '''error_outfile = pyhive.proc.obj.add_file_path("genbank_errors.tsv", True)
    with open(error_outfile, "w") as error_outfh:
        error_outfh.write("Assembly" + "\t" + "Accession" + "\t" + "Protein ID" + "\t" + "ErrorType" + "\t" + "Error Text" + "\t" + "Source Line" + "\n")
        for req in pyhive.proc.grp2req():
            if get_req_data_source(req) == "genbank":
                error_infile = pyhive.proc.req_get_data_path("genbank_errors_individual.tsv", req = req)
                with open(error_infile, "r") as error_infh:
                    error_infh.readline()  # skip header line
                    for error_line in error_infh:
                        error_outfh.wrote(error_line)
                        if (time.time()-progress_timer) >= 300:
                            progress_timer = time.time()
                            pyhive.proc.req_progress(99, 100)'''

    # not done yet - spawn a dna.cgi subrequest to make extended codon table, and wait for it to finish
    launch_extend_codon_table()
    pyhive.proc.req_resubmit(5)
    #pyhive.proc.req_progress(100, 100)
    #pyhive.proc.req_set_status(pyhive.req_status.DONE)

def launch_extend_codon_table():
    extend_codon_table_cmd = pyhive.QPSvc("dnaCGI")
    extend_codon_table_cmd.set_session_id(pyhive.proc.form)
    extend_codon_table_cmd.set_var("cmd", "extendCodonTable")
    extend_codon_table_cmd.set_var("objId", str(pyhive.proc.obj.id))
    extend_codon_table_cmd.set_var("srcName", "main_codon_columns.csv")
    extend_codon_table_req = extend_codon_table_cmd.launch()
    pyhive.proc.req_set_data("extend_codon_table_req", str(extend_codon_table_req))

def find_ionapp_exe():
    try:
        os_name = os.environ["os"]
    except KeyError:
        os_name = "Linux"
    ionapp_exe = distutils.spawn.find_executable("ionapp.os" + os_name)
    if not ionapp_exe:
        ionapp_exe = distutils.spawn.find_executable("ionapp")
    if not ionapp_exe:
        raise OSError("Failed to find ionapp executable")
    return ionapp_exe

def create_codonDB_ions():
    codonDB_csv_path = pyhive.proc.obj.get_file_path("codonDB.csv")
    # ionCodon/ionCodon*.ion - in a subdirectory for compatibility with distributed storage
    ionCodon_dir = pyhive.proc.obj.add_file_path("ionCodon", True)
    os.mkdir(ionCodon_dir)
    ionCodon_basename = os.path.join(ionCodon_dir, "ionCodon")
    ionapp_exe = find_ionapp_exe()
    print("Calling %s -ionCreate %s -ionAlias tbl ionCodon -ionParseTable . %s" % (ionapp_exe, ionCodon_basename, codonDB_csv_path))
    subprocess.check_call([ionapp_exe, "-ionCreate", ionCodon_basename, "-ionAlias", "tbl", "ionCodon", "-ionParseTable", ".", codonDB_csv_path])

def launched_extend_codon_table():
    try:
        return int(str(pyhive.proc.req_get_data("extend_codon_table_req")))
    except:
        return False

def waiting_for_extend_codon_table():
    try:
        status = pyhive.proc.req_get_status(launched_extend_codon_table())
        return status > 0 and status < pyhive.req_status.DONE
    except ValueError:
        return False


'''def genbank_combiner():
    combined_species = {}
    codon_number = {}
    progress_timer = time.time()

    for i in range(0, len(CodonsDict.keys())):
        codon_number[i] = CodonsDict.keys()[i]

    for req in pyhive.proc.grp2req():
        species_infile = pyhive.proc.req_get_data_path("genbank_species.tsv", req = req)
        with open(species_infile, "r") as species_infh:
            species_infh.readline()  # skip header line
            for line in species_infh:
                splitline = line.split("\t")
                species = splitline[4]

                if species not in combined_species.keys():
                    division = splitline[0]
                    assembly = splitline[1]
                    taxid = int(splitline[2])
                    species_taxid = int(splitline[3])
                    if splitline[5] == "True":
                        organellar = True
                    else:
                        organellar = False

                    combined_species[species] = SpeciesCodons(division, assembly, taxid, species_taxid, species, organellar)

                    for i in range(0, len(CodonsDict.keys())):
                        combined_species[species].codons[codon_number[i]] = int(splitline[i+13])

                    combined_species[species].num_included = int(splitline[7])

                    if splitline[6] != "":
                        for translation_table_value in splitline[6].split(","):
                            combined_species[species].transl_table.append(int(translation_table_value.strip()))

                else:
                    combined_species[species].num_included += int(splitline[7])
                    if splitline[6] != "":
                        for translation_table_value in splitline[6].split(","):
                            if int(translation_table_value.strip()) not in combined_species[species].transl_table:
                                combined_species[species].transl_table.append(int(translation_table_value))

                    for i in range(0, len(CodonsDict.keys())):
                        combined_species[species].codons[codon_number[i]] += int(splitline[i+13])

                if (time.time()-progress_timer) >= 300:
                    progress_timer = time.time()
                    pyhive.proc.req_progress(99, 100)

    for key in combined_species.keys():
        combined_species[key].calc_gc()
        if (time.time()-progress_timer) >= 300:
            progress_timer = time.time()
            pyhive.proc.req_progress(99, 100)


    species_outfile = pyhive.proc.obj.add_file_path("genbank_all_species.tsv", True)
    progress_timer = time.time()
    with open(species_outfile, "w") as species_outfh:
        headers = "Division" + "\t" + "Assembly" + "\t" + "Taxid" + "\t" + "Species_Taxid" + "\t" + "Species" + "\t" + "Organellar" + "\t" + "Translation Table" + "\t" + "# CDS" + "\t" + "# Codons" + "\t" + "GC%" + "\t" + "GC1%" + "\t" + "GC2%" + "\t" + "GC3%" + "\t"
        for codon in CodonsDict.keys():
            headers = headers + codon + "\t"
        headers = headers.rstrip() + "\n"
        species_outfh.write(headers)

        for key in combined_species.keys():
            out_string = combined_species[key].format_output()
            species_outfh.write(out_string)
            if (time.time()-progress_timer) >= 300:
                progress_timer = time.time()
                pyhive.proc.req_progress(99, 100)'''
                
                
def bring_to_comb():
    gb_infh = open("o262660-genbank_species.tsv", "r")
    rs_infh = open("o262660-refseq_species.tsv", "r")

    gb_outfh = open(pyhive.proc.obj.add_file_path("genbank_species.tsv", True), "w")
    rs_outfh = open(pyhive.proc.obj.add_file_path("refseq_species.tsv", True), "w")
    
    for line in gb_infh:
        gb_outfh.write(line)
        
    for line in rs_infh:
        rs_outfh.write(line)
        
    gb_infh.close()
    rs_infh.close()
    gb_outfh.close()
    rs_outfh.close()
    
    pyhive.proc.req_progress(100, 100)
    pyhive.proc.req_set_status(pyhive.req_status.DONE)
    

def on_execute(req_id):
    #bring_to_comb()

    if waiting_for_extend_codon_table():
        # extend_codon_table dna.cgi request is running; wait 5 seconds more for it to finish
        pyhive.proc.req_resubmit(5)
        return
    elif launched_extend_codon_table() and pyhive.proc.req_get_status(launched_extend_codon_table()) >= pyhive.req_status.DONE:
        # extend_codon_table dna.cgi request is done; almost done - just need to create codon DB ions
        create_codonDB_ions()
        pyhive.proc.req_progress(100, 100)
        pyhive.proc.req_set_status(pyhive.req_status.DONE)
        return
    elif (len(pyhive.proc.grp2req()) == 1):
        pyhive.proc.req_set_data("data_source", data = "original")
        pyhive.proc.req_set_data("division", data = "original")
        print "starting"
        pull_filelists_ncbi()
        create_all_requests()
        pyhive.proc.req_progress(100, 100)
        pyhive.proc.req_set_status(pyhive.req_status.DONE)
    else:
        pyhive.proc.req_set_data("data_source", data = str(pyhive.proc.form["data_source"]))
        pyhive.proc.req_set_data("division", data = str(pyhive.proc.form["division"]))

        skip_execute = False
        try:
            skip_execute = int(str(pyhive.proc.req_get_data("skip_execute")))
        except:
            pass

        if str(pyhive.proc.form["data_source"]) == "genbank":
            genbank_execute()
        elif str(pyhive.proc.form["data_source"]) == "refseq":
            refseq_execute()

        # Combine individual results files #
        if pyhive.proc.is_last_in_group():
            # don't re-run genbank_execute / refseq_execute - makes debugging simpler when restarting a request
            pyhive.proc.req_set_data("skip_execute", data = "1")
            combine_individual_outputs()  # this function combines identically named species rows
            # combine_individual_outputs() will launch dna.cgi subrequest and resubmit our own request
            return
        else:
            pyhive.proc.req_progress(100, 100)
            pyhive.proc.req_set_status(pyhive.req_status.DONE)









