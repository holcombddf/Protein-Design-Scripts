/*
 * $Id$ ::2B6A7A!
 * Copyright (c) 2005 Dr. Vahan Simonyan and Dr. Raja Mazumder.
 * This software is protected by U.S. Copyright Law and International
 * Treaties. Unauthorized use, duplication, reverse engineering, any
 * form of redistribution, use in part or as a whole, other than by
 * prior, express, written and signed agreement is subject to penalties.
 * If you have received this file in error, please notify copyright
 * holder and destroy this and any other copies. All rights reserved.
 */
#include <qlib/QPrideProc.hpp>
#include <slib/utils.hpp>
#include <ssci/bio.hpp>
#include <violin/violin.hpp>
#include <ssci/bio/biogencode.hpp>
#include <xlib/s_curl.hpp>
#include <xlib/dmlib.hpp>


// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
// _/
// _/  This file demonstrates how to access parameters passed through a form,
// _/  how to locate files in the system, how to access and read,
// _/  sequence and alignment files, how to report progress and how to
// _/  place the results to the proper destination.
// _/
// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/


class CodonUsage : public sQPrideProc
{
        sCurl cm;

        enum enumType
        {
            genomic = 0,
            mitochondrion = 1,
            chloroplast = 2,
            plastid = 3,
            leucoplast = 4,
            chromoplast = 5
        };
        typedef struct
        {
                enumType eType;
                const char *nametype;
                idx nameLength;
                const char letterType;
        } CodonKnownTypes;

    public:

        struct ExonRanges
        {
                idx startCoordinate;
                idx exonLength;
                char strand;
        };
        struct CDS
        {
                const char *proteinID;
                idx proteinIDLength;
                const char *CDSProduct;
                idx CDSProductLength;
                idx translationTable;
                idx codonStartPosition;
                bool pseudo;
                idx exonContainerStartIndex;
                idx exonContainerOffset;
                CDS(){
                    init();
                }
                CDS init(){
                    sSet(this,0);
                    return *this;
                }
        };
        struct GBEntry
        {
                idx taxid;
                const char *speciesName;
                idx speciesNameLength;
                const char *assembly;
                idx assemblyLength;
                const char *sequence;
                idx sequenceLength;
                enumType gType;
                idx locus_offSet, ft_offSet, seq_offSet,end_offSet;
                GBEntry(){
                    sSet(this,0);
                }
                GBEntry init(){
                    sSet(this,0);
                    return *this;
                }
        };
        struct SequenceData
        {
                idx numElements;
                idx codonCounts[65];
                idx bicodonCounts[4097];
                idx dinucleotideCounts[17];
                SequenceData(){
                    sSet(this,0);
                }

        };
        CodonUsage(const char * defline00,const char * srv) : sQPrideProc(defline00,srv)
        {
            downloadDir.cut0cut();
            numtypes = 0;
            while(c_types[++numtypes].nametype);
        }
        sVec <CDS> codingSequences;
        sVec <ExonRanges> exons;
        sVec < sVaxAnnotGB::startEnd> myRangeVec;
        sDic < SequenceData > qryHitRefList;

        sStr entrySequence;
        idx numtypes;
        sStr lbuf;
        static CodonKnownTypes c_types[];

        sStr parserLog, parserMsg;
        sStr downloadDir;


        enumType findTypeID (const char *src, idx typelen = 0)
        {
            idx typeID;

            if( !typelen ) {
                for(typelen = 0; src[typelen]; typelen++) { // until the end of the strings
                    if( src[typelen] == ' ' || src[typelen] == '\n' || src[typelen] == '\r' ) {
                        break;
                    }
                }
            }

            for(typeID = 0; typeID < numtypes; ++typeID) {
                if( typelen == c_types[typeID].nameLength && strncmp(c_types[typeID].nametype, src, typelen) == 0 ) {
                    return c_types[typeID].eType;
                }
            }
            return genomic;
        }


        const char * findAssembly(const char *src, const char *srcEnd, CodonUsage::GBEntry &entry);
        const char * extractGenomeType(const char * srcStart, const char * srcEnd, CodonUsage::GBEntry & entry);
        void extractScientificName(const char * srcStart, const char * srcEnd, CodonUsage::GBEntry & entry);
        const char * extractFeatures(const char * srcStart, const char * srcEnd, CodonUsage::GBEntry & entry);
        void collectInfo(const char * src, CodonUsage::GBEntry & entry,CodonUsage::CDS & cdsList );
        const char * extractCDSInfo (const char *src,const char *srcEnd, CDS * newCDS);
        const char * extractCDSRange (const char *src,const char *srcEnd, CDS * newCDS);
        bool extractCDSSeq (sStr &currSeq, CDS *newCDS);
        bool getCodonInfofromSequence (sStr &seq, SequenceData &seqData, idx startOffset);
        idx getCodonIndex(const char * seq, idx sizeComb);
        const char *getNextEntry (const char *src, const char *srcend, GBEntry &entry);
        const char * getNextFileToDownload (const char *currlistpos, const char *endlistFile, sStr &urlFilePath);
        const char * downloadFile (const char *urlFlnm, const char *gzflnm, sStr &inputFilePath, sStr &error, bool uncompress = false);
        idx parseGB (const char *src, idx srclen, sFil &outFile);
        virtual idx OnExecute(idx);

        bool reqInitFile(sMex & fil, const char * name, const char *ext, sStr * path_buf = 0)
        {
            static sStr local_path_buf;
            if( !path_buf ) {
                path_buf = &local_path_buf;
            }
            const char * path = reqAddFile(*path_buf, "%s%s", name, ext);
            if( path && fil.init(path) && fil.ok() ) {
#ifdef _DEBUG
                logOut(eQPLogType_Trace, "Created %s", path);
#endif
                return true;
            } else {
                logOut(eQPLogType_Error, "Failed to create %s%s", name, ext);
                return false;
            }
        }

        bool printBiCodonTable (sFil *outFile, SequenceData *seqData)
        {
            // Header
            outFile->addString("index, count\n");
            for (idx i = 0; i < (idx)sizeof(seqData->bicodonCounts)/(idx)sizeof(idx); ++i){
                outFile->addNum(i+1);
                outFile->add(",", 1);
                outFile->addNum(seqData->bicodonCounts[i]);
                outFile->add("\n", 1);
//                outFile->printf("%" DEC ",%" DEC "\n", i+1, seqData->bicodonCounts[i] );
            }
            outFile->add0cut();
            return true;

        }

        const char *generateKey(GBEntry &entry)
        {

            lbuf.cut(0);
            bool refseq = entry.assemblyLength > 0 ? true : false;
            //
            if (refseq){
                // Refseq
                // assembly + organelle
                lbuf.add(entry.assembly, entry.assemblyLength);
            }
            else {
                // Genbank
                // scientific name + organelle
                lbuf.add(entry.speciesName, entry.speciesNameLength);
            }
            lbuf.add("-",1);
            lbuf.addString(c_types[entry.gType].nametype);

            return lbuf.ptr(0);
        }

        const char * const getWorkDir(bool algo = false)
        {
            static sStr workDir;
            workDir.cut0cut(0);
            cfgStr(&workDir, 0, "qm.tempDirectory");
            if( workDir ) {
                workDir.printf("%s-%" DEC "/%s", svc.name, reqId, "");
            }
            return workDir;
        }

        const char * const getDownloadsDir(bool algo = false)
        {
            if (downloadDir.length()){
                return downloadDir;
            }
            cfgStr(&downloadDir, 0, "refseq_processor.downloads");
            return downloadDir;
        }

};



static const char* skipToNextLine(const char *buf, const char *bufend)
{
    while (buf < bufend && *buf && *buf != '\r' && *buf != '\n')
        buf++;
    while (buf < bufend && (*buf == '\r' || *buf == '\n'))
        buf++;
    return buf;
}

static const char* skipToNextWord(const char *buf, const char *bufend)
{
    while (buf < bufend && *buf && *buf == ' '){
        buf++;
    }
    return buf;
}

void scanUntilNextLine (sStr & dest, const char * body, const char * srcEnd)
{
    idx recordSize = 0;
    dest.cut(0);
    while (body+(recordSize)<srcEnd){
        while(body+(recordSize)<srcEnd && strchr(sString_symbolsEndline,body[recordSize])==0 ){ // read until end of Line
            ++(recordSize);
        }
        idx i =1;
        while((body+(recordSize) + i)<srcEnd && strchr(sString_symbolsBlank,body[recordSize+i]) ){ // skip blank space
            ++i;
        }
        dest.addString(body,recordSize);
        if (i<10) {  // it is not the continuous of the previous line
            return;
        }

        if (strchr("/",body[recordSize+i]) ) { // it is not the continuous of the previous line
            return;
        }
        body=sShift(body,recordSize + i);
        recordSize=0;
    }
    return;
}



CodonUsage::CodonKnownTypes CodonUsage::c_types[] = {
    {
        genomic,
        "genomic" __,
        7,
        'G' },
    {
        mitochondrion,
        "mitochondrion" __,
        13,
        'M' },
    {
        chloroplast,
        "chloroplast" __,
        11,
        'C' },
    {
        plastid,
        "plastid",
        7,
        'P' },
    {
        leucoplast,
        "leucoplast" __,
        9,
        'L' },
    {
        chromoplast,
        "chromoplast" __,
        11,
        'O' } };


const char * CodonUsage::findAssembly(const char *src, const char *srcEnd, GBEntry &entry){
    const char *p = "\n";
    const char *assemblypos = 0;

    for(; src < srcEnd && !assemblypos; p = src, ++src) {
        if( *p == '\n' || *p == '\r' || src == srcEnd - 1 ) { // first choice is for windows and unix, the second is for mac, the third is end of file
            if( *p == '\r' && src < srcEnd - 1 && *src == '\n' ) {
                ++src;
            }
            if (src && *src != ' '){
                break;
            }
            src = skipToNextWord(src, srcEnd);

            if (strncmp(src, "Assembly: ", 10) == 0){
                assemblypos = src+10;
            }
        }
    }

    if (assemblypos){
        src = assemblypos;
        entry.assembly = src;
        entry.assemblyLength = 0;
        while( *src != '\n' && *src != '\r' ) {
            src++;
            entry.assemblyLength++;
        }
    }
    else {
        entry.assembly = 0;
        entry.assemblyLength = 0;
    }
    return src;
}

const char * CodonUsage::extractCDSInfo (const char *srcStart, const char * srcEnd,CDS * newCDS)
{
    const char *p = "\n";
    const char * src = extractCDSRange(srcStart, srcEnd, newCDS);
    src = skipToNextLine(src, srcEnd);
    for(; src < srcEnd; p = src, ++src) {
        if( *p == '\n' || *p == '\r' || src == srcEnd - 1 ) { // first choice is for windows and unix, the second is for mac, the third is end of file
            if( *p == '\r' && src < srcEnd - 1 && *src == '\n' ) {
                ++src;
            }
            src = skipToNextWord(src, src+5);

            if (src && *src != ' '){
                break;
            }
            src = skipToNextWord(src, src+31);

            if (strncmp(src, "/transl_table=", 14) == 0){
                // translation table
                src += 14;
                newCDS->translationTable = atoidx(src);
            }
            if (strncmp(src, "/codon_start=", 13) == 0){
                // codon start i.e. frame
                src += 13;
                newCDS->codonStartPosition = atoidx(src);
            }
            if (strncmp(src, "/product=\"", 10) == 0){
                // product i.e. protein name
                // check for low quality here
                src += 10;
                newCDS->CDSProduct =src;
                newCDS->CDSProductLength = 0;
                while (*src != '"'){
                    src++;
                    newCDS->CDSProductLength++;
                }

            }
            if (strncmp(src, "/protein_id=\"", 13) == 0){
                // protein_id i.e. protein accession number
                src += 13;
                newCDS->proteinID = src;
                newCDS->proteinIDLength = 0;
                while (*src != '"'){
                    src++;
                    newCDS->proteinIDLength++;
                }

            }
            if (strncmp(src, "/pseudo", 7) == 0 || strncmp(src, "/pseudogene", 11) == 0){
                newCDS->pseudo = true;
            }
        }

    }
    return src;
}

const char * CodonUsage::extractCDSRange (const char *src, const char * srcEnd,CDS * newCDS)
{
    sStr reserveBuf;
    scanUntilNextLine(reserveBuf, src, srcEnd);

    bool checkJoin = (strncmp("join",reserveBuf.ptr(0),4)==0) ? true : false;
    bool checkOrder = (strncmp("order",reserveBuf.ptr(0),5)==0) ? true : false;

//    sVaxAnnotGB gbhandler;
    newCDS->exonContainerStartIndex = myRangeVec.dim();
    if (checkJoin || checkOrder){
           if (checkOrder){
               sVaxAnnotGB::parseJoinOrOrder(reserveBuf.ptr(0), myRangeVec,"order(");
           }
           else {
               sVaxAnnotGB::parseJoinOrOrder(reserveBuf.ptr(0), myRangeVec);
           }
           if (myRangeVec.dim() - newCDS->exonContainerStartIndex) {
               newCDS->exonContainerOffset = myRangeVec.dim() - newCDS->exonContainerStartIndex;
           }
    }
    else {
        bool checkComplement = (strncmp("complement",reserveBuf.ptr(0),10)==0) ? true : false;
        if (checkComplement) {
            sVaxAnnotGB::parseComplement(reserveBuf.ptr(0), myRangeVec);
            if( myRangeVec.dim() - newCDS->exonContainerStartIndex ) {
                newCDS->exonContainerOffset = myRangeVec.dim() - newCDS->exonContainerStartIndex;
            }
        }
        else {
            sVaxAnnotGB::startEnd *range = myRangeVec.add();
            char * nxt;
            if( *src == '>' || *src == '<' ){++src;}
            range->start = strtoidx(src, &nxt, 10);
            if( strncmp(nxt, "..", 2) == 0 ) {
                src = nxt + 2; // start..end
                if( *src == '>' || *src == '<' )
                    ++src;
                range->end = strtoidx(src, &nxt, 10);
            } else{
                range->end = range->start;
            }
            newCDS->exonContainerOffset = 1;
        }
    }
    return src;
}

bool CodonUsage::extractCDSSeq(sStr &out, CDS *newCDS)
{

    for (idx irange = 0; irange < newCDS->exonContainerOffset; ++irange){
        sVaxAnnotGB::startEnd *range =myRangeVec.ptr(newCDS->exonContainerStartIndex + irange);

        const char *start = entrySequence.ptr(range->start-1);
        idx rangelen = range->end - range->start + 1;
        idx outlength = out.length();
        out.add(start, rangelen);
        if (!range->forward){
            idx revll = rangelen - 1;
            char * rev = out.ptr(outlength);
            char * tt = entrySequence.ptr(range->start-1);
            for(idx ll = 0; ll < rangelen; ++ll, --revll) {
                tt[ll] = sBioseq::mapRevATGC[sBioseq::mapComplementATGC[sBioseq::mapATGC[(idx) rev[revll]]]];
            }
        }
    }
    return true;
}

bool CodonUsage::getCodonInfofromSequence (sStr &seq, SequenceData &seqData, idx startOffset)
{
    idx currCodon = 0;
    idx currDinuc = 0;
    idx prevCodon = getCodonIndex(seq.ptr(0), 3);
    if (prevCodon<0){
        seqData.codonCounts[64] += 1;
    }
    else{
        seqData.codonCounts[prevCodon] += 1;
    }
    for (const char * ptr = seq.ptr(0); ptr < seq.ptr(seq.length()-3); ptr += 3){
        currCodon = getCodonIndex(ptr+3, 3);
        currDinuc = getCodonIndex(ptr+2, 2);

        if (currCodon < 0){
            seqData.codonCounts[64] += 1;
            seqData.bicodonCounts[4096] += 1;
        }
        else{
            seqData.codonCounts[currCodon] += 1;
            if (prevCodon>=0){
                seqData.bicodonCounts[(prevCodon*64)+currCodon] += 1;
            }
            else{
                seqData.bicodonCounts[4096] += 1;
            }

        }

        if (currDinuc<0){
            seqData.dinucleotideCounts[16] += 1;
        }
        else {
            seqData.dinucleotideCounts[currDinuc] += 1;
        }

        prevCodon = currCodon;
    }

    return true;

}

inline idx CodonUsage::getCodonIndex(const char * seq, idx sizeComb)
{
    idx base = 1;
    idx sum = 0;
    for(idx i = sizeComb - 1; 0 <= i; i--) {
        char ch = sBioseq::mapATGC[(idx)seq[i]];
        if (ch > 3){
            return -1;
        }
        sum += ch * base;
        base *= 4;
    }
    return sum;
}

const char * CodonUsage::extractFeatures(const char * srcStart, const char * srcEnd, CodonUsage::GBEntry & entry)
{
    const char * src = srcStart;
    const char *p = "\n";
    idx isSource = 0;
    const char * f = "source"_"CDS"__; // watch prefixes
    idx flen[] = {6, 3};
    // 1 source
    // 2 CDS

    for(; src < srcEnd; p = src, ++src) {
        if( *p == '\n' || *p == '\r' || src == srcEnd - 1 ) { // first choice is for windows and unix, the second is for mac, the third is end of file
            if( *p == '\r' && src < srcEnd - 1 && *src == '\n' ) {
                ++src;
            }

            // skip the first 5 character
            src = skipToNextWord(src, src+5);

            // Extract taxid
            //
            if (src && *src != ' '){
                isSource = 0;
                idx iter=0;
                for (const char * ft=f; ft ; ft=sString::next00(ft), ++iter) {
                    if(strncmp(src, ft, flen[iter]) == 0){
                        isSource = iter+1;
                        break;
                    }
                }
            }
            src = sString::skipWords(src, 0, 0, " ");

            if( (isSource == 1) && (strncmp(src, "/db_xref=\"", 10) == 0) && entry.taxid == 0) {
                    src += 10;
                    if( strncmp(src, "taxon:", 6)==0) {
                        src += 6;
                        entry.taxid = atoidx(src);
                    } else {
                        entry.taxid = 0;
                    }
            }
            if(isSource == 2){
                // Here we have found a new CDS, extract ranges
                CDS *newCDS = codingSequences.add(1);
                newCDS->init();
                src = sString::skipWords(src+3, 0, 0, " ");
                src = extractCDSInfo (src, srcEnd,newCDS);
                bool isValid = true;
                // Should we keep the newCDS ?
                const char * retString = sString::searchSubstring(newCDS->CDSProduct, newCDS->CDSProductLength, "LOW QUALITY" __, 1, 0, false);

                if (retString){
                    // no valid
                    isValid = false;
                }
                else if (newCDS->pseudo == true){
                    isValid = false;
                }
                if (!isValid) {
                   // delete CDS from entry/containers?
                    codingSequences.cut(-1);
                }
                isSource = 0;
            }
        }

    }
    return src;
}

const char * CodonUsage::extractGenomeType(const char * srcStart, const char * srcEnd, CodonUsage::GBEntry & entry)
{
    const char * src = srcStart, *p = "\n";

    for(; src < srcEnd; p = src, ++src) {
        if( *p == '\n' || *p == '\r' || src == srcEnd - 1 ) { // first choice is for windows and unix, the second is for mac, the third is end of file
            if( *p == '\r' && src < srcEnd - 1 && *src == '\n' ) {
                ++src;
            }

            if( strncmp(src, "SOURCE", 6) == 0 ) {
//                src = skipToNextWord(src, srcEnd);

                src = sString::skipWords(src, 0, 0, " ");
                entry.gType = findTypeID(src);
                // move srcpointer to the end
                src += sLen(c_types[entry.gType].nametype);
                return src;
            }
        }
    }
    return src;
}


void CodonUsage::extractScientificName(const char * srcStart, const char * srcEnd, CodonUsage::GBEntry & entry)
{
    const char * src = srcStart, *p = "\n";

    for(; src < srcEnd; p = src, ++src) {
        if( *p == '\n' || *p == '\r' || src == srcEnd - 1 ) { // first choice is for windows and unix, the second is for mac, the third is end of file
            if( *p == '\r' && src < srcEnd - 1 && *src == '\n' ) {
                ++src;
            }
            src = skipToNextWord (src, srcEnd);
            if( strncmp(src, "ORGANISM", 8) ) {
                src = sString::skipWords(src+8, 0, 0, " ");

                entry.speciesName = src;  //mark start position of name
                entry.speciesNameLength = 0;
                while( *src != '\n' && *src != '\r' ) {
                    src++;
                    entry.speciesNameLength++;
                }
            }

        }
    }
}

void CodonUsage::collectInfo(const char * src, CodonUsage::GBEntry & entry,CodonUsage::CDS & cdsList ) {
    extractGenomeType(src+entry.locus_offSet, src+entry.ft_offSet,entry);
    extractScientificName(src+entry.locus_offSet, src+entry.ft_offSet,entry);
    extractFeatures(src+entry.ft_offSet,src+entry.seq_offSet,entry);
    entrySequence.cut(0);
    // src and seq_offset must be at ORIGIN to get the actual sequence
    sVioseq2::extractGBSequence(src+entry.seq_offSet,entrySequence);
}

const char * CodonUsage::getNextEntry(const char *src, const char *srcend, GBEntry &entry)
{

    const char * entryStart = src, *p = "\n";
    udx numEntries = 0;
    for(; src < srcend; p = src, ++src) {
        if( *p == '\n' || *p == '\r' || src == srcend - 1 ) { // first choice is for windows and unix, the second is for mac, the third is end of file
            if( *p == '\r' && src < srcend - 1 && *src == '\n' ) {
                ++src;
            }
//        while( src < srcend && *src && *src != '\r' && *src != '\n' ) {

//            if( (strncmp(src, "LOCUS", 5) == 0) || (strncmp(src, "\nLOCUS", 6) == 0) ) {
             if( strncmp(src, "  ORGANISM", 10) == 0 ) {
                // the beginning of the Entry
//                entry.locus_offSet = src - entryStart;
                 src = sString::skipWords(src+10, 0, 0, " ");
                 entry.speciesName = src;  //mark start position of name
                 entry.speciesNameLength = 0;
                 while( *src != '\n' && *src != '\r' ) {
                     src++;
                     entry.speciesNameLength++;
                 }
//                extractScientificName(src+10, srcend, entry);
                //src = extractGenomeType(src+5, srcend,entry);
            }
            if( (strncmp(src, "DBLINK", 6) == 0)) {
                src = findAssembly(src+6, srcend, entry);
            }
            if( strncmp(src, "SOURCE", 6) == 0 ) {
                src = sString::skipWords(src+6, 0, 0, " ");
                entry.gType = findTypeID(src);
                // move srcpointer to the end
                src += sLen(c_types[entry.gType].nametype);
            }
            if( strncmp(src, "//", 2) == 0 ) {
                // this is the end of the Entry
                // reparse all needed fields
                entry.end_offSet = src - entryStart;
                break;
            }
            if( strncmp(src, "ORIGIN", 6) == 0 ) {
                // The next line is beginning of the sequence
                entry.seq_offSet = src - entryStart;
                src = sVioseq2::extractGBSequence(src,entrySequence);
                numEntries += 1;
                break;
            }
            if( strncmp(src, "FEATURES", 8) == 0 ) {
                // extract the source feature and CDS features
                entry.ft_offSet = src - entryStart;
                extractFeatures(src,srcend,entry);
            }


        }

    }
    return src;

}

const char * CodonUsage::getNextFileToDownload (const char *src, const char *srcend, sStr &urlFilePath)
{
    // TODO: compare file timestamp to validate that we are getting the most recent version
    const char * entryStart = src, *p = "\n";
    udx numEntries = 0;
    const char *nextrow = 0;
    for(; src < srcend; p = src, ++src) {
        if( *p == '\n' || *p == '\r' || src == srcend - 1 ) { // first choice is for windows and unix, the second is for mac, the third is end of file
            if( *p == '\r' && src < srcend - 1 && *src == '\n' ) {
                ++src;
            }
            nextrow = skipToNextLine(src, srcend);

            // Look for a '|' in the row
            lbuf.cut0cut();
            sString::searchAndReplaceSymbols(&lbuf, src, nextrow - src, "|", 0, 0, true, true, false, false);
            if (lbuf.length() && sString::cnt00(lbuf) > 4){
                // ) If it has '|', we will extract the last value with the pipes
                const char *val = sString::next00(lbuf, 4);
                urlFilePath.addString(val);
                return nextrow;
            }
        }
    }

    return nextrow;
}

const char *CodonUsage::downloadFile (const char *urlFlnm, const char *gzflnm, sStr &inputFilePath, sStr &error, bool uncompress)
{

    const char *retString = gzflnm;

    if (urlFlnm){
        sFil gzInputFile(gzflnm);
        if( !gzInputFile.ok() ) {
            error.printf("Cannot save file: %s", gzflnm);
            return 0;
        }
    //        const char *urlLog = "ftp://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/001/020/275/GCF_001020275.1_Bbif07v4/GCF_001020275.1_Bbif07v4_genomic.gbff.gz";
        const char *urlLog = "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/002/287/175/GCF_002287175.1_ASM228717v1/GCF_002287175.1_ASM228717v1_genomic.gbff.gz";
        cm.cookie_setFile(0);
        sIO *lio = (sIO *) &gzInputFile;
        cm.setIO(lio);
        idx res = cm.Get(urlLog);
        if( res ) {
            // Validate return
            error.printf("error");
        }
    }
//    gzInputFile.add(cm.io->ptr(0), cm.io->length());
    if (uncompress){
        // Uncompress
        dmLib dm;
        parserLog.cut0cut();
        parserMsg.cut0cut();
        dm.unpack(gzflnm, 0, &parserLog, &parserMsg);
        if (!dm.dim()) {
            error.printf("can't uncompress: %s", parserMsg.ptr());
            return 0;
        }
        retString = inputFilePath.addString(dm.first()->location());
    }
    return retString;
}

idx CodonUsage::parseGB (const char *src, idx srclen, sFil &outFile)
{
    // MAIN ALGORITHM:
    //create dictionaries
    //loop through GB files
    // {
    //     while (EOF) {
    //      getEntry metadata
    //      calculate table entries
    //      register keys into dicts
    //      merge entries
    //      clear out codingSequences, exons, entrySequence  (write out to CDS file/empty containers)
    //     }
    // }
    const char * currpos = src;
    const char * endFile = src+srclen;

    GBEntry gbentry;
    sStr currSeq, protSeq;

    while (currpos < endFile){
        gbentry.init();
        entrySequence.cut(0);

        currpos = getNextEntry(currpos, endFile, gbentry);

        // Temporary.. create a file in the obj directory

        // Generate key for gbEntry
        // Generate the key(s) to add to existing dictionaries
        const char * key = generateKey(gbentry);
        //      register keys into dicts
        // Add to dictionaries
        SequenceData * seqData = qryHitRefList.get(key);

        if (!seqData){
            // New Entry in the dictionary
            seqData = qryHitRefList.set(key);
            seqData->numElements = 0;
        }
        seqData->numElements += 1;


        // We should have all the information, so we can start processing the entry
        //      calculate table entries

        for (idx i = 0; i < codingSequences.dim(); i++){
            CDS *curCDS = codingSequences.ptr(i);

            currSeq.cut(0);
            protSeq.cut(0);
            extractCDSSeq (currSeq, curCDS);

            // calculate table entries
            getCodonInfofromSequence(currSeq, *seqData, curCDS->codonStartPosition);

//            printBiCodonTable (&outFile, seqData);

    //        // Translate into protein
    //        char *seq = currSeq.ptr(0);
    //        for (idx icod = 0; icod < currSeq.length(); icod += 3 ){
    //            const char *a = sBioseq::codon2AA(seq, curCDS->translationTable)->print(sBioseq::eBioAAsingle);
    //            protSeq.add(a, 1);
    //            seq += 3;
    //        }
        }

        // Go back for a new entry
    }
    // Print all the info for gbentry into Outfile/dictiionary
    return 0;

}

idx CodonUsage::OnExecute(idx req)
{

#ifdef _DEBUG
    for (idx i=0; i<pForm->dim(); i++) {
        const char * key = static_cast<const char*>(pForm->id(i));
        const char * value = pForm->value(key);
        printf("%s = %s\n", key, value);
    }
#endif

    // _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
    // _/
    // _/  Full paths are not exposed to the users so in order to locate a file
    // _/  we do it through their objects. Let assume that an object consists
    // _/  of two files. Then in order to locate the file we call a member
    // _/  function of the object (HIVE objects are described by C++ objects
    // _/  so we use the term "object" interchangeably ). So a C++ object is
    // _/  constructed based on a HIVE's object ID and then we get the path of
    // _/  file associated to the object.
    // _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/

    const sHiveId objID = objs[0].Id();

    std::auto_ptr < sUsrObj > obj(user->objFactory(objID));

    if( !obj.get() || !obj->Id() ) {
        logOut(eQPLogType_Info, "Object %s not found or access denied", objID.print());
        reqSetInfo(req, eQPInfoLevel_Error, "Object %s not found or access denied", objID.print());
        return 1;
    } else {
        logOut(eQPLogType_Info, "processing object %s\n", objID.print());
    }

    // Prepare working directory
    const char * const wd = getWorkDir();
    if( !wd ) {
        reqSetInfo(reqId, eQPInfoLevel_Error, "Missing configuration");
        logOut(eQPLogType_Error, "Could not create working directory");
        reqSetStatus(reqId, eQPReqStatus_ProgError);
        return 0;
    }
    sDir::removeDir(wd);
    if( !sDir::makeDir(wd) ) {
        reqSetInfo(reqId, eQPInfoLevel_Error, "Cannot establish working directory");
        reqSetStatus(reqId, eQPReqStatus_ProgError);
        return 0;
    }
    reqProgress(-1,1,100);

    progress100Start = 1;
    progress100End = 10;

    // Read params
    sHiveId genbankHiveId (formValue("genbank_sourceFile", 0));

    sUsrFile gbObjId(genbankHiveId, user);

    sStr listFilePath;
    gbObjId.getFile(listFilePath);

    ::printf("We have the list file: %s", listFilePath.ptr(0));

    sFil listFileSource (listFilePath.ptr(0), sMex::fReadonly);

    if (listFileSource.length() == 0) {
        // Error: Empty file
        reqSetInfo(reqId, eQPInfoLevel_Error, "List File is empty or access denied");
        reqSetStatus(reqId, eQPReqStatus_ProgError);
        return 0;
    }

    // Prepare output table file
    sFil outFile;
    if( !reqInitFile(outFile, "bicodonTable", ".csv") ) {
        reqSetStatus(req, eQPReqStatus_ProgError);
        return 0;
    }

    //    refseq_processor.downloads
    // Prepare downloading directory
    sStr downloadFlnm("%s%s.%s", getWorkDir(), "name", "gz");

    const char * currlistpos = listFileSource.ptr();
    const char * endlistFile = listFileSource.ptr()+listFileSource.length();


    sStr urlFilePath, error, inputGBfilepath;
    sFilePath p, downloadFilePath;
    sFil gbSource;
    idx counter = 0;
    while (currlistpos < endlistFile && counter < 5){
        urlFilePath.cut0cut();
        error.cut0cut();
        gbSource.cut(0);
        currlistpos = getNextFileToDownload (currlistpos, endlistFile, urlFilePath);

        // Check that the file is already in the system
        p.cut0cut(0);
        p.makeName(urlFilePath, "%%flnmx"); // p is "dir/subdir/file-2.txt.bck"
        sStr flnm("%s%s.%s", getWorkDir(), "name", "gz");

        downloadFilePath.cut0cut(0);
        downloadFilePath.printf("%s/%s.gz", getDownloadsDir(), p.ptr());
        const char *inputfilepathname = 0;
        if (sFile::exists(downloadFilePath)){
            // uncompress the file
            inputfilepathname = downloadFile (0, downloadFilePath.ptr(), inputGBfilepath, error, true);
        }
        else {
            // Download the file
            inputfilepathname = downloadFile (urlFilePath.ptr(), flnm.ptr(), inputGBfilepath, error, true);

        }

        // Prepare sFil to keep download file
//        sFil gzInputFile(flnm.ptr());
//        if( !gzInputFile.ok() ) {
//            error.printf("Cannot save file: %s", flnm.ptr());
//            return 0;
//        }

        if (!inputfilepathname){
            reqSetInfo(reqId, eQPInfoLevel_Error, "%s", error.ptr(0));
            reqSetStatus(reqId, eQPReqStatus_ProgError);
            return 0;
        }
        gbSource.init(inputfilepathname, sMex::fReadonly);
        if( !gbSource.ok() ) {
            reqSetInfo(reqId, eQPInfoLevel_Error, "Cannot access downloaded file: %s", inputfilepathname);
            reqSetStatus(reqId, eQPReqStatus_ProgError);
            return 0;
        }

        if (error.length()){
            // Report warning
        }

        // Parse GB file and start accumulating entries
        parseGB (gbSource.ptr(), gbSource.length(), outFile);
        ++counter;
    }



//    logOut(eQPLogType_Debug,"\n::::::::::::::::: login :::::::::::::::::\n%.*s\n:::::::::::::::::::::::::::::::::::::::::\n",(int)cm.io->length(),cm.io->ptr(0));

    //    filename.cut(0);
//    sQPrideProc::reqAddFile(filename, ".demo.sumInDels.csv");
//    sFil indel_file(filename); // make a file object ... where we can print
//
//    indel_file.printf("Indel,count\n");
//    indel_file.printf("Insertions,%" DEC "\nDeletions,%" DEC, insertions, deletions);
//

    reqProgress(1, 100, 100);
    reqSetStatus(req, eQPReqStatus_Done);

    return 0;
}


int main(int argc, const char * argv[])
{
    sBioseq::initModule(sBioseq::eACGT);

    sStr tmp;
    sApp::args(argc,argv); // remember arguments in global for future

    CodonUsage backend("config=qapp.cfg" __,sQPrideProc::QPrideSrvName(&tmp,"codon-usage",argv[0]));
    return (int)backend.run(argc,argv);
}

/*
 * Debugging
 * ----------
 *
 * command used:gdb
 * example: gdb --args ./dna-demo grab 1234
 * 1234 is the request id that will be used.
 * once inside gdb we can run the executable.
 *
 * run <args>: the command that runs the executable (if args are missing then
 * those that were passed on gdb call will be used.
 *
 * break <file>:<line #> : will create a breakpoint with an incremental number being its ID.
 * condition <breakpoint ID> <expression> creates a conditional breakpoint/
 * ignore <breakpoint ID> <number> : will ignore the breakpoint <number> of times
 * disable <breakpoint ID> : will disable the breakpoint (or all of them if <breakpoint ID> is not provided)
 * delete <breakpoint ID> : will delete the breakpoint (or all of them if <breakpoint ID> is not provided)
 * print <variable> :will print variable
 * info break <breakpoint ID> : tells how many time the breakpoint has been hit
 * next (n): moves to the next line
 * step (s): steps inside the line
 * finish : step out
 * continue (c) : continue until next breakpoint (or end)
 * list 41 : list the lines centered around 41
 * list (l) : show the 'n' next lines
 * set listsize n : sets listsize 'n'
 * quit (q) : exits gdb
 * backtrace (bt) : shows the frames
 * up/down <n> : navigate <n> frames  up/down. Missing default n=1.
 *
 */


