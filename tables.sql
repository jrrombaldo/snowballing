
CREATE TABLE papers (
    id VARCHAR(64),
    title VARCHAR(256) NOT NULL, 
    paper JSON,
    ris JSON,
    source VARCHAR(32) CHECK( source IN ('RIS','SBF','SBB') ),
    stat VARCHAR(32) CHECK( stat IN ('FOUND', 'NOT_FOUND','DETAILS_NOT_FOUND') )
)


-- FOUND means it was able to find a match on semantic scholar given the RIS paper
-- NOT_FOUND - opposite of above
-- DETAILS_NOT_FOUND - it was able to  find the paper, but could not get its details (this should not happen)