#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml import etree
from lxml.builder import ElementMaker

class CheckIdentifierNodeResult:    
    correction = False
    xml = ""    

def replaceText(md, oldvalue, newvalue):
    return md.replace(oldvalue, newvalue)

def checkIdentifierNode (xml):
    result = CheckIdentifierNodeResult()
    ns={'gmd':  'http://www.isotc211.org/2005/gmd',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmx':  'http://www.isotc211.org/2005/gmx'}      
    fileidentifier = xml.xpath('/gmd:MD_Metadata/gmd:fileIdentifier/gco:CharacterString/text()',namespaces=ns)    
    identifier = xml.xpath('/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:MD_Identifier/gmd:code/gco:CharacterString/text()',namespaces=ns)
    if len(identifier)>0:
        #all is ok
        print "ok"
    else:
        #Pas d'itentifier        
        #test de présence du noeud non conforme
        badNode = xml.find('.//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier',namespaces=ns)
        #création noeud identifier
        E = ElementMaker(namespace="http://www.isotc211.org/2005/gmd",nsmap={'gmd' : "http://www.isotc211.org/2005/gmd"})
        S = ElementMaker(namespace="http://www.isotc211.org/2005/gco",nsmap={'gco' : "http://www.isotc211.org/2005/gco"})
        V=S.CharacterString
        E1=E.identifier
        E2=E.MD_Identifier
        E3=E.code
        newNode = E1(E2(E3(V(fileidentifier[0]))))       
        if badNode is not None:
            #Si noeud incorrect
            print "   ---> %s mauvais noeud" % fileidentifier[0]
            #Récupération du noeud parent
            parentNode = badNode.getparent()
            #Suppression du mauvais noeud
            parentNode.remove(badNode)            
        else:
            #Si pas de noeud
            print "   ---> %s absence de noeud" % fileidentifier[0]
            #Récupération du noeud parent
            parentNode = xml.find('.//gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation',namespaces=ns)
                 
        
        #ajout du nouveau noeud et création du nouveau fichier
        parentNode.append(newNode)        
        result.correction = True
        result.xml= etree.tostring(xml, pretty_print=True)
    return result
        

