#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import logging
import abc
import sys
from dataclasses import dataclass
import keyring
from bs4 import BeautifulSoup

class Institution():
    """
    Wayforward and idp values for service provider
    
    """
    TUC = {
           'acro': "TUC",
           'wayf': 16, #<! Wayforward for OPAL
           'idp': 2 #<! idp for VCS
           }
    

@dataclass
class Shibboleth:
    _username = None
    _password = None
    _SAMLResponse = None
    _headers = {
        #'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/96.0'
        }
    _post = {}
    _user_idp = None
    _institution = None
    session = requests.Session()
    
    def setUser(self, username: str):
        self._username = username
        self._password = keyring.get_password("system", self._username)
        


class ServiceProviderInterface(metaclass = abc.ABCMeta):
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'connect') and callable(subclass.conect)
                and hasattr(subclass, 'login') and callable(subclass.login)
                and hasattr(subclass, 'setup') and callable(subclass.setup)
                and hasattr(subclass, 'JSHandler') and callable(subclass.JSHandler)
                and hasattr(subclass, 'url') and hasattr(subclass, 'name') 
                or NotImplemented)
    
    @property
    def url(self):
        return self._url
    
    @property
    def shib(self):
        return self._shib
    
    
    @abc.abstractmethod
    def connect(self, shib: Shibboleth) -> Shibboleth:
        """ must be implemented """
        
        return NotImplementedError
    
class TUCServiceProvider(ServiceProviderInterface):
    """
    Implements logic for connecting to TUC.
    
    """
    
    
    url = 'https://www.tu-chemnitz.de/tu/wtc/index.html'
    shib = None
    # _krbUrl is used for bypassing the Google Captcha
    _krbUrl = "https://wtc.tu-chemnitz.de/krb/module.php/core/loginuserpass.php?AuthState="
    
    def __init__(self, shib = None):
        self.shib = shib
        self.shib._institution = Institution.TUC
        self.shib._post["TUC"] = 'https://www.tu-chemnitz.de/Shibboleth.sso/SAML2/POST'
        self.shib._user_idp = 'https://wtc.tu-chemnitz.de/shibboleth'

    def connect(self) -> Shibboleth:
        
        logging.info("Logging into TU Chemnitz.")
        
        if self.shib._SAMLResponse:
            logging.info("SAMLResponse was found. No need to connect again.")
            return self.shib
        
        response = self.shib.session.get(self.url, headers=self.shib._headers)
        response = self.shib.session.post(response.url, data = {
            'session':'true', 'user_idp': self.shib._user_idp,
            'Select':''})
        
        # Circumvent JavaScript redirection
        soup = BeautifulSoup(response.text, 'html.parser') 
        target = soup.find('a', {'id':  'redirect'}).get('href')
        response = self.shib.session.get(target)
               
        
        soup = BeautifulSoup(response.text, 'html.parser') 
        AuthState = soup.find('input', {'name':  'AuthState'}).get('value')
        response = self.shib.session.post(response.url, data = {'username': self.shib._username,
                                                        'AuthState': AuthState})
        response = self.shib.session.post(self._krbUrl+AuthState, 
                                  data = {'password': self.shib._password})
        response = self.shib.session.post(response.url, params = {'yes':''})

        soup = BeautifulSoup(response.text, 'html.parser') 
        self.shib._SAMLResponse =  soup.find('input', {'name':  'SAMLResponse'}).get('value')
        response = self.shib.session.post(self.shib._post["TUC"], data = {'SAMLResponse': self.shib._SAMLResponse})
        
        return self.shib
    
class OPALServiceProvider(ServiceProviderInterface):
    url = "https://bildungsportal.sachsen.de/opal/"
    _RelayState = "https://bildungsportal.sachsen.de/opal/shibboleth/?ajax=true"
    shib = None
    
    def __init__(self, shib: Shibboleth):
        self.shib = shib
        self.shib._post["OPAL"] = 'https://bildungsportal.sachsen.de/dfn/Shibboleth.sso/SAML2/POST'
    
    def connect(self) -> Shibboleth:
        
        logging.info("Logging into OPAL.")
        
        if not self.shib._SAMLResponse:
            logging.error("No SAMLResponse found. Exiting program.")
            sys.exit(1)
            
        response = self.shib.session.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        target = soup.find('form', {'id':  'id10'}).get('action') # Find wayf target
        response = self.shib.session.post(self.url[0:-6]+target, data = {'wayfselection': self.shib._institution["wayf"], 
                                                    'shibLogin': ''})
        response = self.ShibAuthHandler(response)
        
        return self.shib
        
    def ShibAuthHandler(self, response = None):
        """
        Different institutions may have different authentification services that
        are intertwined with Shibboleth. For example, TU Chemnitz uses Kerberos.
        
        """
        if(self.shib._institution["acro"] == Institution.TUC["acro"]):
            response = self.shib.session.post(response.url, params = {'yes':''})
            soup = BeautifulSoup(response.text, 'html.parser')
            self.shib._SAMLResponse = soup.find('input', {'name':  'SAMLResponse'}).get('value')
            response = self.shib.session.post(self.shib._post["OPAL"], data = {'RelayState': self._RelayState, 
                                                                       'SAMLResponse': self.shib._SAMLResponse})    
            return response
        

class VCSServiceProvider(ServiceProviderInterface):
    url = 'https://videocampus.sachsen.de/login'
    shib = None 
    
    def __init__(self, shib: Shibboleth):
        self.shib = shib
        self.shib._post["VCS"] = 'https://videocampus.sachsen.de/saml/acs'
    
    def connect(self): 
        
        logging.info("Logging into Video Campus Sachsen.")
        
        if not self.shib._SAMLResponse:
            logging.error("No SAMLResponse found. Exiting program.")
            sys.exit(1)
            
    
        response = self.shib.session.get(self.url[0:-6]+'/saml/login',
                                    params = {'idp':self.shib._institution["idp"] })
        
        response = self.ShibAuthHandler(response)
        return self.shib
    
    def ShibAuthHandler(self, response = None):
        """
        Different institutions may have different authentification services that
        are intertwined with Shibboleth. For example, TU Chemnitz uses Kerberos.
        
        """
        if(self.shib._institution["acro"] == Institution.TUC["acro"]):
            response = self.shib.session.post(response.url, params = {'yes':''})
            soup = BeautifulSoup(response.text, 'html.parser')
            self.shib._SAMLResponse = soup.find('input', {'name':  'SAMLResponse'}).get('value')
            RelayState = soup.find('input', {'name':  'RelayState'}).get('value')
            response = self.shib.session.post(self.shib._post["VCS"], data = {'SAMLResponse': self.shib._SAMLResponse,
                                                                              'RelayState': RelayState})   

           
            return response
             
