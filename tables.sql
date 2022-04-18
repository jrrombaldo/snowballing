CREATE TABLE papers
(
    id     VARCHAR(64),
    title  VARCHAR(256) NOT NULL,
    paper  JSON,
    ris    JSON,
    source VARCHAR(32) CHECK ( source IN ('RIS', 'SB') ),
    stat   VARCHAR(32) CHECK ( stat IN ('FOUND', 'NOT_FOUND', 'DETAILS_NOT_FOUND') )
);

CREATE VIEW snowballing AS
SELECT title,
       json_array_length(paper, '$.references') AS reference,
       json_array_length(paper, '$.citations')  AS citations
FROM papers
WHERE stat = 'FOUND'
  AND source = 'RIS';


CREATE VIEW snowballing_round AS
SELECT
    json_extract(value, '$.paperId') AS id,
    json_extract(value, '$.title') AS title
FROM (
    SELECT value FROM papers, json_each(papers.paper, '$.citations')
    UNION ALL
    SELECT value FROM papers, json_each(papers.paper, '$.references')
     )
WHERE
    id IS NOT NULL
    AND id NOT IN (SELECT id FROM papers WHERE stat = 'FOUND');