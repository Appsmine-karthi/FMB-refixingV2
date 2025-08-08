with open("log.txt",'r') as f:
    gh = f.readlines()
    with open("log_filtered.txt",'w') as f2:
        for line in gh:
            if "{'error_type'" in line:
                f2.write(line)