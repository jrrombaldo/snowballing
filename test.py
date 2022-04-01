from snowballing.scholarsemantic import ScholarSemantic


if __name__ == "__main__":
    for paper_tuple in ScholarSemantic().get_extracted_papers_to_snowball('both'):
        print (paper_tuple)