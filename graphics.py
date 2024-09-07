import matplotlib
matplotlib.use('Agg')

def pie(column, output_path):
    # plt.figure()
    import matplotlib.pyplot as plt
    labels = column.unique()
    d = [column.value_counts()[i] for i in labels]
    plt.pie(d, labels=labels, autopct='%1.1f%%')
    plt.legend()
    plt.savefig(output_path)
    plt.close()


def hist(column, output_path):
    import matplotlib.pyplot as plt
    # plt.figure()
    plt.hist(column)
    plt.savefig(output_path)
    plt.close()


def plot(*args, output_path):
    import matplotlib.pyplot as plt
    # plt.figure()
    plt.plot(args)
    plt.savefig(output_path)
    plt.close()