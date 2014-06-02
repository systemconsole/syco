  DocumentRoot /var/www/html/

  ErrorLog logs/rentalfront-ssl-error_log
  CustomLog logs/rentalfront-ssl-access_log combined

  # Ignore /sec from root proxy.
  ProxyPass /sec !

  # Start rewrite engine
  RewriteEngine on

  # Rewrite all cookies.
  ProxyPassReverseCookiePath / /

  # Pass the Host: line from the incoming request to the proxied host,
  # instead of the hostname specified in the ProxyPass line.
  ProxyPreserveHost On

  # Prevents Apache from functioning as a forward proxy server
  ProxyRequests Off

  # Every proxy request will have all its Via: header lines removed.
  ProxyVia Block

  <Proxy *>
    Order deny,allow
    Allow from all
  </Proxy>

  #
  # Require SSL to view thease pages.
  #
  SSLEngine on
  SSLProtocol -all +SSLv3 +TLSv1
  SSLHonorCipherOrder On
  SSLCipherSuite ECDHE-RSA-AES128-SHA256:AES128-GCM-SHA256:RC4:HIGH:!MD5:!aNULL:!EDH
  SSLCertificateFile /etc/httpd/ssl/ssl-rentalfront/wild.fareoffice.com.crt
  SSLCertificateKeyFile /etc/httpd/ssl/ssl-rentalfront/wild.fareoffice.com.key
  SSLCertificateChainFile /etc/httpd/ssl/ssl-rentalfront/ca/geotrust-ca.pem