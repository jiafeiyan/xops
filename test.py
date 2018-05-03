md_source = '/Users/chenyan/CompanyProjects/xops/sim_data/md.csv'
with open(md_source, 'rb') as f:
    for row in f.readlines()[1:3]:
        if "\n" in row:
            row = row.replace("\n", "").split(",")
            print row
