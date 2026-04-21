FROM ontotext/graphdb:10.7.0

USER root

# Create the repository directory structure
RUN mkdir -p /opt/graphdb/home/data/repositories

# Copy pre-unzipped GEMR repository directly
COPY endPoint/GEMR /opt/graphdb/home/data/repositories/GEMR

# Overwrite config.ttl with the correct version
COPY config.ttl /opt/graphdb/home/data/repositories/GEMR/config.ttl

# Expose the default GraphDB port
EXPOSE 7200
