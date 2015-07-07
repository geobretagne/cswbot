# cswbot
Scripts de modification par lots de métadonnées via csw

## Prerequis

 * Python > 2.6
 * lxml (librairie pyhon) [Windows] (https://pypi.python.org/pypi/lxml/3.2.3)
 
 
## Usage

exemple de commande pour effectuer un rechercher remplacer sur toutes les métadonnées du catalogue:

    cswbot.py --url=http://geobretagne.fr/geonetwork/srv/fre/csw --user=**** --password=**** --oldvalue="@region-bretagne.fr" --newvalue="@bretagne.bzh" --where=all



## Paramètres requis

    --url=[URL] url du service csw
    --user=[USER] utilisateur du catalogue
    --password=[PASSWORD] Mot de passe utilisateur du catalogue    
    --oldvalue=[VALUE] Valeur de texte à remplacer
    --newvalue=[VALUE] Valeur de remplacement
    --where=[FILTER] Filtre permettant de sélectionner les métadonnées à mettre à jour. ex :
        any=OGC:WMS,
        identifier=2cbe6fe0-9176-11de-bf1a-0000c0a8230c
        organisationName=CG22,
        all
    

## Paramètres optionnels
       
    --connected [mode Connecté], permet de sélectionner toutes les métadonnées y compris celles qui ne sont pas publiées
    --maxrecords=[MAX] the MAX records returned by CSW getRecords OPERATION
    --proxy=[PROXY] Proxy à utiliser pour accéder à Internet ex : http://127.0.0.1:8888 ou http://user:password@192.168.1.1:8080

