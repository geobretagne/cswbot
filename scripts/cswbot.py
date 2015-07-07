#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import sys, urllib2, base64, getopt, os, logging
from lxml import etree
from io import StringIO, BytesIO
from datetime import datetime
import cswtools
#Globals
transactions = []
transactions_errors = []
transactions_success = []
transactions_no_update = []

def usage():
    print """
    %s [options]

Required Parameters
-------------------

    --url=[URL] the URL of the CSW
    --user=[USER] the USER of the CSW
    --password=[PASSWORD] the PASSWORD of the CSW    
    --oldvalue=[VALUE] the VALUE to replace
    --newvalue=[VALUE] the new VALUE
    --where=[FILTER] the FILTER of the CSW default is no filter. ex :
        any=OGC:WMS,
        organisationName=CG22,
        all
    

Optional Parameters
-------------------           
    --connected [MODE CONNECTED]
    --maxrecords=[MAX] the MAX records returned by CSW getRecords OPERATION
    --proxy=[PROXY] the proxy to use for internet access e.g http://127.0.0.1:8888 or http://user:password@192.168.1.1:8080

Example
-------------------
python cswbot.py --url=http://dev.geobretagne.fr/geonetwork/srv/fre/csw --user=yyy --password=xxx  --oldvalue=Concarno --newvalue=Concarno --where="any=Concarno" --connected

""" % sys.argv[0]
    

def httpRequest(url, body, headers, autenticate, user, password, proxy):
    requestTimeout = 600
    proxyHandler =None
    if proxy == False:
        proxyHandler = urllib2.ProxyHandler()
    else:
        proxyHandler = urllib2.ProxyHandler({'http':proxy})
    opener = urllib2.build_opener(urllib2.HTTPHandler(), proxyHandler)
    urllib2.install_opener(opener)
    request = urllib2.Request(url, body, headers)
    if (autenticate):        
        base64string = base64.encodestring('%s:%s' % (user, password)).replace('\n', '')        
        request.add_header("Authorization", "Basic %s" % base64string)        
   
    try:
        response = urllib2.urlopen(request, timeout=requestTimeout)        
        result = response.read().decode('utf-8', errors='strict').encode('utf-8')  
        
        try:            
            #xmlResponse = parseString(result)
            xmlResponse = etree. fromstring(result)            
        except Exception, e:            
            xmlResponse = False
            print "Error parsing xml :" 
            logging.debug("Error parsing xml " )
            logging.debug( result.encode('utf-8'))
            pass        
        return xmlResponse
    except urllib2.HTTPError, e:
        print "Erreur HTTP " + str(e.code)
        #logging.debug( e.read().encode('utf-8'))
        if e.code == 401:
            sys.exit(4)
        else:
            return False
    

def completeUpdate(user, password, url, metadataID, title, MD_Metadata, XML_Metadata,oldvalue, newvalue):
    global transactions_errors
    global transactions_success
    global transactions_no_update
    ns={'gmd':  'http://www.isotc211.org/2005/gmd','gco': 'http://www.isotc211.org/2005/gco', 'gmx':  'http://www.isotc211.org/2005/gmx','csw':'http://www.opengis.net/cat/csw/2.0.2'}   
    headers = {"Content-type": "application/xml"}
    cswpostbody = '''<?xml version="1.0" encoding="UTF-8"?>
        <csw:Transaction service="CSW" version="2.0.2" xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" xmlns:ogc="http://www.opengis.net/ogc" 
            xmlns:apiso="http://www.opengis.net/cat/csw/apiso/1.0">
            <csw:Update>
            %s
            </csw:Update>
        </csw:Transaction>''' % (cswtools.replaceText(MD_Metadata,str(oldvalue), str(newvalue)))

    xmlResponse = httpRequest(url, cswpostbody, headers, True, user, password, proxy)
    print xmlResponse
    if xmlResponse is not None:
        #totalupdated = int(xmlResponse.getElementsByTagName('csw:totalUpdated')[0].childNodes[0].data)
        totalupdated = int(xmlResponse.xpath('/csw:TransactionResponse/csw:TransactionSummary/csw:totalUpdated/text()', namespaces=ns)[0])       
        if (totalupdated > 0):
            print 'success for metadata :' + metadataID
            transactions_success.append(unicode(metadataID + ": " + title))
        else:            
            print 'no update for metadata :' + metadataID
            transactions_no_update.append(unicode(metadataID + ": " + title))

    else:
        print 'Error for metadata :' + metadataID
        transactions_errors.append(unicode(metadataID + ": " + title))


def main(url ,user, password, where, oldvalue, newvalue, maxrecords, connected, proxy):
    global transactions
    global transactions_errors
    global transactions_success
    global transactions_no_update       
    headers = {"Content-type": "application/xml"}
    ns={'gmd':  'http://www.isotc211.org/2005/gmd','gco': 'http://www.isotc211.org/2005/gco', 'gmx':  'http://www.isotc211.org/2005/gmx','csw':'http://www.opengis.net/cat/csw/2.0.2'} 
    lastPageReached = False           
    startPosition = 1    
    page = 0
    nbpages = 0
    proceededRecords = 0
    
    print "start : csw proceeded : " + url + "..."
    logging.info("start : csw proceeded : " + url + "...")
    print 'getting metadatas...'
    while not lastPageReached:
        ogcfilter = None
        if where == 'all':
            ogcfilter = ''
        else:            
            if where.find('=') > -1:
                ogcfilter = '''<csw:Constraint version="1.1.0">
                                <Filter xmlns="http://www.opengis.net/ogc" xmlns:gml="http://www.opengis.net/gml" >
                                    <PropertyIsEqualTo>
                                        <PropertyName>%s</PropertyName>
                                        <Literal>%s</Literal>
                                    </PropertyIsEqualTo>                    
                              </Filter>
                            </csw:Constraint>''' % (where.split("=")[0], where.split("=")[1])
            else:
                print "where parameter uses invalid operator, no filter will applied"
        
        
        cswpostbody = '''<?xml version="1.0"?>
            <csw:GetRecords xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" service="CSW" version="2.0.2"
                resultType="results" outputSchema="csw:IsoRecord" maxRecords="%s" startPosition="%s">
                <csw:Query typeNames="gmd:MD_Metadata">        
                        <csw:ElementSetName>full</csw:ElementSetName>
                %s
                </csw:Query>
            </csw:GetRecords>''' % (str(maxrecords), str(startPosition), ogcfilter)  
                
        if connected:
            xmlResponse = httpRequest(url, cswpostbody, headers, True, user, password, proxy)
        else:
            xmlResponse = httpRequest(url, cswpostbody, headers, False, None, None, proxy)
        if xmlResponse:            
            recordsMatched = int(xmlResponse.xpath('/csw:GetRecordsResponse/csw:SearchResults', namespaces=ns)[0].get("numberOfRecordsMatched"))            
            recordsReturned = int(xmlResponse.xpath('/csw:GetRecordsResponse/csw:SearchResults', namespaces=ns)[0].get("numberOfRecordsReturned"))
            recordNext = int(xmlResponse.xpath('/csw:GetRecordsResponse/csw:SearchResults', namespaces=ns)[0].get("nextRecord"))            
            page += 1
            if (proceededRecords == 0):
                nbpages = recordsMatched / maxrecords
                if (recordsMatched % maxrecords > 0):
                    nbpages+= 1
            progress = ""
            if (recordsReturned == recordsMatched):
                progress = "Step 1 to " + str(nbpages)
                lastPageReached = True
            elif (recordNext > recordsMatched):
                progress = "Last step"
                lastPageReached = True
            else:
                progress = "Step " + str(page) + " to " + str(nbpages)
                startPosition = recordNext
                lastPageReached = False
                
            print progress
           
            #metadatas = xmlResponse.getElementsByTagName('gmd:MD_Metadata')
            metadatas = xmlResponse.xpath('/csw:GetRecordsResponse/csw:SearchResults/gmd:MD_Metadata',namespaces=ns)
            if metadatas:
                for metadata in metadatas:
                    typeMD= metadata.find('.//gmd:hierarchyLevel/gmd:MD_ScopeCode',namespaces=ns).get('codeListValue')
                    #check if metadata is dataset medatada and not service metadata
                    if typeMD=='dataset':
                        #identifier = unicode(metadata.getElementsByTagName("gmd:fileIdentifier")[0].getElementsByTagName("gco:CharacterString")[0].childNodes[0].data)
                        identifier = unicode(metadata.find('.//gmd:fileIdentifier/gco:CharacterString',namespaces=ns) .text  )
                        #title = unicode(metadata.getElementsByTagName("gmd:identificationInfo")[0].getElementsByTagName("gmd:title")[0].getElementsByTagName("gco:CharacterString")[0].childNodes[0].data)
                        title = unicode(metadata.find('.//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString',namespaces=ns).text)
                        #strMetadata = str(metadata.toprettyxml(indent="", newl="", encoding="utf-8"))
                        strMetadata = etree.tostring(metadata, pretty_print=True)
                        if strMetadata.find(oldvalue)>-1:
                            #completeUpdate(user, password, url + '-publication', identifier, title, strMetadata, oldvalue, newvalue)
                            transactions.append({'identifier' : identifier, 'title': title, 'metadata': strMetadata, 'metadataXML':metadata})
                        else:
                            transactions_no_update.append(unicode(identifier + ": " + title))
                    
            
            proceededRecords += recordsReturned
            print '-----------------------------------------------------------------------'
            print str(proceededRecords) + " Medatadas downloaded on "  + str(recordsMatched)
            print '-----------------------------------------------------------------------'
        else:
            #print "Aucune metadata for this request :"
            sys.exit()
            
    print 'update transactions...'
    for transaction in transactions:
         completeUpdate(user, password, url + '-publication', transaction['identifier'], transaction['title'], transaction['metadata'],transaction['metadataXML'], oldvalue, newvalue)
         
    logging.info('Report')
    logging.info( 'metadata IDs Errors : ' + '\n'.join(transactions_errors).encode('utf-8'))
    logging.info('----------------------------------------------------------------------------------')
    logging.info( 'metadata IDs not updated : ' + '\n'.join(transactions_no_update).encode('utf-8'))
    logging.info('----------------------------------------------------------------------------------')
    logging.info( 'metadata IDs Success : ' + '\n'.join(transactions_success).encode('utf-8'))
    logging.info('----------------------------------------------------------------------------------')
    logging.info('Total metadatas proceeded : ' + str(proceededRecords).encode('utf-8'))

    print '---------------------Report----------------------------'
    print 'metadata  Errors : ' + str(len(transactions_errors))
    print '-------------------------------------------------------'
    print 'metadata  not updated : ' + str(len(transactions_no_update))
    print '-------------------------------------------------------'
    print 'metadata  Success : ' + str(len(transactions_success))
    print '-------------------------------------------------------'
    print 'Total metadatas proceeded : ' + str(proceededRecords)
    print '-------------------------------------------------------'
                  
            

if __name__ == "__main__":
    if len(sys.argv) == 1:
        usage()
        sys.exit()
    else:
        try:
            path = os.getcwd()
            logname=path + '/' +datetime.now().strftime('log_cswbot_%Y_%m_%d_%H_%M.log')                    
            logging.basicConfig(filename=logname,level=logging.DEBUG)            
            opts, args = getopt.getopt(sys.argv[1:], '', ['url=', 'user=', 'password=', 'oldvalue=', 'newvalue=', 'connected', 'where=', 'proxy='])           
        except getopt.GetoptError, err:            
            print str(err)
            usage()
            sys.exit(2)
            
        url = None
        where = None
        oldvalue = None
        newvalue = None
        user = None
        password = None
        maxrecords = 20
        connected = False
        proxy = False

        # set args
        for o, a in opts:
            if o == '--connected':                
                connected = True
            elif o in '--url':
                url = a
            elif o in '--where':
                where = a
            elif o in '--oldvalue':
                oldvalue = a
            elif o in '--newvalue':
                newvalue = a
            elif o in '--user':
                user = a
            elif o in '--password':
                password = a
            elif o in '--proxy':
                proxy = a
            elif o in '--maxrecords':
                maxrecords = int(a)            
            else:
                assert False, 'unhandled option'

        if url is None or oldvalue is None or newvalue is None or password is None or user is None or where is None:
            usage()
            sys.exit(3)
        else:
            logging.info(' '.join(sys.argv).replace(user,'******').replace(password,'****'))
            main(url ,user, password, where, oldvalue, newvalue, maxrecords, connected, proxy)
