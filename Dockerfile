# docker build --no-cache -t syco .
# docker run -it --rm -v "$PWD":/opt/syco syco
FROM centos:6
RUN yum -y update && \
    yum -y install iptables pexpect python-crypto && \
    yum clean all
ADD . /opt/syco
RUN /opt/syco/bin/syco.py install-syco
CMD ["/bin/bash"]