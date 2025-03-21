@description('Tipo de datos para los parámetros de ruta en la operación GET de la API de copias de seguridad')
param operations_get_handle_http_type string = 'string'

@description('Tipo de datos para los parámetros de ruta en la operación POST de la API de copias de seguridad')
param operations_post_handle_http_type string = 'string'

@description('Tipo de datos para el parámetro subscriptionId en la operación majorupgrade')
param operations_majorupgrade_type string = 'string'

@description('Tipo de datos para el parámetro resourcegroup en la operación majorupgrade')
param operations_majorupgrade_resourcegroup_type string = 'string'

@description('Tipo de datos para el parámetro servername en la operación majorupgrade')
param operations_majorupgrade_servername_type string = 'string'

@description('Tipo de datos para el parámetro api-version en la operación majorupgrade')
param operations_majorupgrade_apiversion_type string = 'string'

@description('Nombre del servicio de API Management')
param apiManagementServiceName string = 'apimservice'

@description('Nombre de la API de gestión de copias de seguridad')
param backupApiName string = 'dumprestore'

@description('Nombre de la API de actualización de versiones')
param upgradeApiName string = 'majorversionupgrade'

@description('Nombre de la Function App que actúa como backend')
param functionAppName string = 'functionapp'

@description('ID de suscripción donde se encuentra la Function App')
param functionAppSubscriptionId string = '00000000-0000-0000-0000-000000000000'

@description('Ruta base para la API de copias de seguridad')
param backupApiPath string = 'dumprestore'

@description('Ruta base para la API de actualización de versiones')
param upgradeApiPath string = 'major'

@description('URL base de la Function App')
param functionAppUrl string = 'https://${functionAppName}.azurewebsites.net'

@description('Ubicación/región donde se implementarán los recursos')
param location string = 'UK South'

@description('Nombre del grupo de recursos donde se implementarán los recursos')
param resourceGroupName string = 'myResourceGroup'

@description('Plantilla para la ruta de recursos del servidor PostgreSQL Flexible')
param flexibleServerPathTemplate string = '/subscriptions/{subscriptionId}/resourceGroups/{resourcegroup}/providers/Microsoft.DBforPostgreSQL/flexibleServers/{servername}'

resource apimService 'Microsoft.ApiManagement/service@2024-06-01-preview' = {
  name: apiManagementServiceName
  location: location
  sku: {
    name: 'Developer'
    capacity: 1
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publisherEmail: 'contact@example.com'
    publisherName: 'Contoso'
    notificationSenderEmail: 'apimgmt-noreply@mail.windowsazure.com'
    hostnameConfigurations: [
      {
        type: 'Proxy'
        hostName: '${apiManagementServiceName}.azure-api.net'
        negotiateClientCertificate: false
        defaultSslBinding: true
        certificateSource: 'BuiltIn'
      }
    ]
    customProperties: {
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls10': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls11': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Ssl30': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Ciphers.TripleDes168': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls10': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls11': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Ssl30': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Protocols.Server.Http2': 'False'
    }
    virtualNetworkType: 'None'
    disableGateway: false
    apiVersionConstraint: {}
    publicNetworkAccess: 'Enabled'
  }
}

// dumprestore API
resource backupApi 'Microsoft.ApiManagement/service/apis@2024-06-01-preview' = {
  parent: apimService
  name: backupApiName
  properties: {
    displayName: backupApiName
    apiRevision: '1'
    description: 'API para gestión de copias de seguridad'
    subscriptionRequired: true
    path: backupApiPath
    protocols: [
      'https'
    ]
    authenticationSettings: {
      oAuth2AuthenticationSettings: []
      openidAuthenticationSettings: []
    }
    subscriptionKeyParameterNames: {
      header: 'Ocp-Apim-Subscription-Key'
      query: 'subscription-key'
    }
    isCurrent: true
  }
}

// majorversionupgrade API
resource upgradeApi 'Microsoft.ApiManagement/service/apis@2024-06-01-preview' = {
  parent: apimService
  name: upgradeApiName
  properties: {
    displayName: upgradeApiName
    apiRevision: '1'
    description: 'Major Version Upgrade API for Azure PostgreSQL Flexible Server'
    subscriptionRequired: false
    serviceUrl: 'https://management.azure.com/'
    path: upgradeApiPath
    protocols: [
      'https'
    ]
    authenticationSettings: {
      oAuth2AuthenticationSettings: []
      openidAuthenticationSettings: []
    }
    subscriptionKeyParameterNames: {
      header: 'Ocp-Apim-Subscription-Key'
      query: 'subscription-key'
    }
    isCurrent: true
  }
}

// Backend for dumprestore API
resource functionAppBackend 'Microsoft.ApiManagement/service/backends@2024-06-01-preview' = {
  parent: apimService
  name: functionAppName
  properties: {
    description: functionAppName
    url: functionAppUrl
    protocol: 'http'
    resourceId: 'https://management.azure.com/subscriptions/${functionAppSubscriptionId}/resourceGroups/${resourceGroupName}/providers/Microsoft.Web/sites/${functionAppName}'
    credentials: {
      header: {
        'x-functions-key': [
          '{{${functionAppName}-key}}'
        ]
      }
    }
  }
}

// Operations for dumprestore API
resource backupApiGetOperation 'Microsoft.ApiManagement/service/apis/operations@2024-06-01-preview' = {
  parent: backupApi
  name: 'get-handle-http'
  properties: {
    displayName: 'handle_http'
    method: 'GET'
    urlTemplate: '/{route}'
    templateParameters: [
      {
        name: 'route'
        required: true
        values: []
        type: operations_get_handle_http_type
      }
    ]
    responses: []
  }
}

resource backupApiPostOperation 'Microsoft.ApiManagement/service/apis/operations@2024-06-01-preview' = {
  parent: backupApi
  name: 'post-handle-http'
  properties: {
    displayName: 'handle_http'
    method: 'POST'
    urlTemplate: '/{route}'
    templateParameters: [
      {
        name: 'route'
        required: true
        values: []
        type: operations_post_handle_http_type
      }
    ]
    responses: []
  }
}

// Operation for majorversionupgrade API
resource upgradeApiOperation 'Microsoft.ApiManagement/service/apis/operations@2024-06-01-preview' = {
  parent: upgradeApi
  name: 'majorupgrade'
  properties: {
    displayName: 'majorupgrade'
    method: 'PATCH'
    urlTemplate: flexibleServerPathTemplate
    templateParameters: [
      {
        name: 'subscriptionId'
        required: true
        values: []
        type: operations_majorupgrade_type
      }
      {
        name: 'resourcegroup'
        required: true
        values: []
        type: operations_majorupgrade_resourcegroup_type
      }
      {
        name: 'servername'
        required: true
        values: []
        type: operations_majorupgrade_servername_type
      }
    ]
    request: {
      queryParameters: [
        {
          name: 'api-version'
          defaultValue: '2024-11-01-preview'
          values: [
            '2024-11-01-preview'
          ]
          type: operations_majorupgrade_apiversion_type
        }
      ]
      headers: []
      representations: []
    }
    responses: []
  }
}

// Policies for dumprestore API operations
resource backupApiGetPolicy 'Microsoft.ApiManagement/service/apis/operations/policies@2024-06-01-preview' = {
  parent: backupApiGetOperation
  name: 'policy'
  properties: {
    value: '<policies>\r\n  <inbound>\r\n    <base />\r\n    <set-backend-service id="apim-generated-policy" backend-id="${functionAppName}" />\r\n  </inbound>\r\n  <backend>\r\n    <base />\r\n  </backend>\r\n  <outbound>\r\n    <base />\r\n  </outbound>\r\n  <on-error>\r\n    <base />\r\n  </on-error>\r\n</policies>'
    format: 'xml'
  }
}

resource backupApiPostPolicy 'Microsoft.ApiManagement/service/apis/operations/policies@2024-06-01-preview' = {
  parent: backupApiPostOperation
  name: 'policy'
  properties: {
    value: '<policies>\r\n  <inbound>\r\n    <base />\r\n    <set-backend-service id="apim-generated-policy" backend-id="${functionAppName}" />\r\n  </inbound>\r\n  <backend>\r\n    <base />\r\n  </backend>\r\n  <outbound>\r\n    <base />\r\n  </outbound>\r\n  <on-error>\r\n    <base />\r\n  </on-error>\r\n</policies>'
    format: 'xml'
  }
}
