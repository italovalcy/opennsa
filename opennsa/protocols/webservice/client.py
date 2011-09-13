"""
Web Service protocol for OpenNSA.

Author: Henrik Thostrup Jensen <htj@nordu.net>
Copyright: NORDUnet (2011)
"""

import uuid

from twisted.python import log

from opennsa.protocols.webservice.ext import twistedsuds


WSDL_PROVIDER   = 'file:///home/htj/nsi/opennsa/wsdl/ogf_nsi_connection_provider_v1_0.wsdl'
WSDL_REQUESTER  = 'file:///home/htj/nsi/opennsa/wsdl/ogf_nsi_connection_requester_v1_0.wsdl'


URN_UUID_PREFIX = 'urn:uuid:'

def createCorrelationId():
    return URN_UUID_PREFIX + str(uuid.uuid1())


class ProviderClient:

    def __init__(self, reply_to):

        self.reply_to = reply_to
        self.client = twistedsuds.TwistedSUDSClient(WSDL_PROVIDER)


    def _createGenericRequestType(self, requester_nsa, provider_nsa, connection_id):

        req = self.client.createType('{http://schemas.ogf.org/nsi/2011/07/connection/types}GenericRequestType')
        req.requesterNSA = requester_nsa.urn()
        req.providerNSA  = provider_nsa.urn()
        req.connectionId = connection_id
        return req


    def reservation(self, correlation_id, requester_nsa, provider_nsa, session_security_attr, global_reservation_id, description, connection_id, service_parameters):

        res_req = self.client.createType('{http://schemas.ogf.org/nsi/2011/07/connection/types}ReservationType')

        res_req.requesterNSA                = requester_nsa.urn()
        res_req.providerNSA                 = provider_nsa.urn()

        #<sessionSecurityAttr>
        #    <ns5:Attribute NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic" Name="globalUserName">
        #        <ns5:AttributeValue xsi:type="xs:string" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">jrv@internet2.edu</ns5:AttributeValue>
        #    </ns5:Attribute>
        #    <ns5:Attribute NameFormat="urn:oasis:names:tc:SAML:2.0:attrname-format:basic" Name="role">
        #        <ns5:AttributeValue xsi:type="xs:string" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">AuthorizedUser</ns5:AttributeValue>
        #    </ns5:Attribute>
        #</sessionSecurityAttr>

        # OK, giving up for now, SUDS refuses to put the right namespace on this
        #user_attr = self.client.createType('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute')
        #user_attr._Name = 'globalUserName'
        #user_attr._NameFormat = 'urn:oasis:names:tc:SAML:2.0:attrname-format:basic'
        #user_attr.AttributeValue = ['jrv@internet2.edu']
        #role_attr = self.client.createType('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute')
        #role_attr._Name = 'role'
        #role_attr._NameFormat = 'urn:oasis:names:tc:SAML:2.0:attrname-format:basic'
        #role_attr.AttributeValue = ['AuthorizedUser']
        #res_req.sessionSecurityAttr['Attribute'] = [ user_attr, role_attr ]

        res_req.reservation.globalReservationId     = global_reservation_id
        res_req.reservation.description             = description
        res_req.reservation.connectionId            = connection_id

        res_req.reservation.path.directionality     = service_parameters.directionality
        res_req.reservation.path.sourceSTP.stpId    = service_parameters.source_stp.urn()
        #res_req.reservation.path.sourceSTP.stpSpecAttrs.guaranteed = ['123' ]
        #res_req.reservation.path.sourceSTP.stpSpecAttrs.preferred =  ['abc', 'def']
        res_req.reservation.path.destSTP.stpId      = service_parameters.dest_stp.urn()

        res_req.reservation.serviceParameters.schedule.startTime    = service_parameters.start_time
        res_req.reservation.serviceParameters.schedule.endTime      = service_parameters.end_time
        res_req.reservation.serviceParameters.bandwidth.desired     = service_parameters.bandwidth_params.desired
        res_req.reservation.serviceParameters.bandwidth.minimum     = service_parameters.bandwidth_params.minimum
        res_req.reservation.serviceParameters.bandwidth.maximum     = service_parameters.bandwidth_params.maximum
        #res_req.reservation.serviceParameters.serviceAttributes.guaranteed = [ '1a' ]
        #res_req.reservation.serviceParameters.serviceAttributes.preferred  = [ '2c', '3d' ]

        d = self.client.invoke(provider_nsa.url(), 'reservation', correlation_id, self.reply_to, res_req)
        return d


    def provision(self, correlation_id, requester_nsa, provider_nsa, session_security_attr, connection_id):

        req = self._createGenericRequestType(requester_nsa, provider_nsa, connection_id)
        d = self.client.invoke(provider_nsa.url(), 'provision', correlation_id, self.reply_to, req)
        return d


    def release(self, correlation_id, requester_nsa, provider_nsa, session_security_attr, connection_id):

        req = self._createGenericRequestType(requester_nsa, provider_nsa, connection_id)
        d = self.client.invoke(provider_nsa.url(), 'release', correlation_id, self.reply_to, req)
        return d


    def terminate(self, correlation_id, requester_nsa, provider_nsa, session_security_attr, connection_id):

        req = self._createGenericRequestType(requester_nsa, provider_nsa, connection_id)
        d = self.client.invoke(provider_nsa.url(), 'terminate', correlation_id, self.reply_to, req)
        return d


    def query(self, correlation_id, requester_nsa, provider_nsa, session_security_attr, operation="Summary", connection_ids=None, global_reservation_ids=None):

        req = self.client.createType('{http://schemas.ogf.org/nsi/2011/07/connection/types}QueryType')
        #print req

        req.requesterNSA = requester_nsa.urn()
        req.providerNSA  = provider_nsa.urn()
        req.operation = operation
        req.queryFilter.connectionId = connection_ids or []
        req.queryFilter.globalReservationId = global_reservation_ids or []
        #print req

        d = self.client.invoke(provider_nsa.url(), 'query', correlation_id, self.reply_to, req)
        return d




class RequesterClient:

    def __init__(self):

        self.client = twistedsuds.TwistedSUDSClient(WSDL_REQUESTER)


    def _createGenericConfirmType(self, requester_nsa, provider_nsa, global_reservation_id, connection_id):

        conf = self.client.createType('{http://schemas.ogf.org/nsi/2011/07/connection/types}GenericConfirmedType')
        conf.requesterNSA        = requester_nsa
        conf.providerNSA         = provider_nsa
        conf.globalReservationId = global_reservation_id
        conf.connectionId        = connection_id
        return conf


    def reservationConfirmed(self, requester_uri, correlation_id, requester_nsa, provider_nsa, global_reservation_id, description, connection_id, service_parameters):

        #correlation_id = self._createCorrelationId()

        res_conf = self.client.createType('{http://schemas.ogf.org/nsi/2011/07/connection/types}ReservationConfirmedType')

        res_conf.requesterNSA   = requester_nsa
        res_conf.providerNSA    = provider_nsa

        res_conf.reservation.globalReservationId    = global_reservation_id
        res_conf.reservation.description            = description
        res_conf.reservation.connectionId           = connection_id
        #res_conf.reservation.connectionState        = 'Reserved' # not sure why this doesn't work

        res_conf.reservation.serviceParameters.schedule.startTime     = service_parameters.start_time.isoformat()
        res_conf.reservation.serviceParameters.schedule.endTime       = service_parameters.end_time.isoformat()

        res_conf.reservation.serviceParameters.bandwidth.desired      = service_parameters.bandwidth_params.desired
        res_conf.reservation.serviceParameters.bandwidth.minimum      = service_parameters.bandwidth_params.minimum
        res_conf.reservation.serviceParameters.bandwidth.maximum      = service_parameters.bandwidth_params.maximum

        res_conf.reservation.path.directionality  = service_parameters.directionality
        res_conf.reservation.path.sourceSTP.stpId = service_parameters.source_stp.urn()
        res_conf.reservation.path.destSTP.stpId   = service_parameters.dest_stp.urn()

        d = self.client.invoke(requester_uri, 'reservationConfirmed', correlation_id, res_conf)
        return d


    def reservationFailed(self, requester_uri, correlation_id, requester_nsa, provider_nsa, global_reservation_id, connection_id, connection_state, error_msg):

        res_fail = self.client.createType('{http://schemas.ogf.org/nsi/2011/07/connection/types}GenericFailedType')
        nsi_ex   = self.client.createType('{http://schemas.ogf.org/nsi/2011/07/connection/types}NsiExceptionType')

        res_fail.requesterNSA   = requester_nsa
        res_fail.providerNSA    = provider_nsa

        res_fail.globalReservationId    = global_reservation_id
        res_fail.connectionId           = connection_id
        res_fail.connectionState        = connection_state

        nsi_ex.messageId = 'OPENNSA_FAILURE'
        nsi_ex.text = error_msg
        res_fail.ServiceException = nsi_ex

        d = self.client.invoke(requester_uri, 'reservationFailed', correlation_id, res_fail)
        return d


    def provisionConfirmed(self, requester_uri, correlation_id, requester_nsa, provider_nsa, global_reservation_id, connection_id):

        conf = self._createGenericConfirmType(requester_nsa, provider_nsa, global_reservation_id, connection_id)
        d = self.client.invoke(requester_uri, 'provisionConfirmed', correlation_id, conf)
        return d

    #def provisionFailed(self, 


    def releaseConfirmed(self, requester_uri, correlation_id, requester_nsa, provider_nsa, global_reservation_id, connection_id):

        conf = self._createGenericConfirmType(requester_nsa, provider_nsa, global_reservation_id, connection_id)
        d = self.client.invoke(requester_uri, 'releaseConfirmed', correlation_id, conf)
        return d

    #def releaseFailed(self, 


    def terminateConfirmed(self, requester_uri, correlation_id, requester_nsa, provider_nsa, global_reservation_id, connection_id):

        conf = self._createGenericConfirmType(requester_nsa, provider_nsa, global_reservation_id, connection_id)
        d = self.client.invoke(requester_uri, 'terminateConfirmed', correlation_id, conf)
        return d

    #def terminateFailed(self, 

    def queryConfirmed(self, requester_uri, correlation_id, requester_nsa, provider_nsa, operation, connections):

        res = self.client.createType('{http://schemas.ogf.org/nsi/2011/07/connection/types}QueryConfirmedType')
        res.requesterNSA = requester_nsa
        res.providerNSA  = provider_nsa

        if operation == "Summary":
            qsrs = []
            for conn in connections:
                qsr = self.client.createType('{http://schemas.ogf.org/nsi/2011/07/connection/types}QuerySummaryResultType')
                #print qsr
                qsr.globalReservationId = conn.global_reservation_id
                qsr.description         = conn.description
                qsr.connectionId        = conn.connection_id
                qsr.connectionState     = conn.state()

                qsr.path.sourceSTP.stpId    = conn.source_stp.urn()
                qsr.path.destSTP.stpId      = conn.dest_stp.urn()

                qsr.serviceParameters.schedule.startTime = conn.service_parameters.start_time
                qsr.serviceParameters.schedule.endTime   = conn.service_parameters.end_time

                qsr.serviceParameters.bandwidth.desired  = conn.service_parameters.bandwidth_params.desired
                qsr.serviceParameters.bandwidth.minimum  = conn.service_parameters.bandwidth_params.minimum
                qsr.serviceParameters.bandwidth.maximum  = conn.service_parameters.bandwidth_params.maximum

                qsrs.append(qsr)

            res.reservationSummary = qsrs

        elif operation == "Details":
            qdr = self.client.createType('{http://schemas.ogf.org/nsi/2011/07/connection/types}QueryDetailsResultType')
            #print qdr
            qdr.globalReservationId = '123'
            res.reservationDetails = [ qdr ]

        else:
            raise ValueError('Invalid query operation type')

        d = self.client.invoke(requester_uri, 'queryConfirmed', correlation_id, res)
        return d


    def queryFailed(self, requester_uri, correlation_id, requester_nsa, provider_nsa, *args):
        print "CLIENT QUERY FAILED"


