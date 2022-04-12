
CREATE TABLE papers (
    id VARCHAR(64),
    title VARCHAR(256) NOT NULL, 
    paper JSON,
    ris JSON,
    source VARCHAR(32) CHECK( source IN ('RIS','SBF','SBB') ),
    stat VARCHAR(32) CHECK( stat IN ('FOUND', 'NOT_FOUND','DETAILS_NOT_FOUND') )
)
