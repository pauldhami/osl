# This script will be used for the mass-labeling event of the MEGUK partnership data - July 2021
# It intends to speed up the process by loading in the data based on a data name, clearing ica.exclude, plotting the
# components interactively, and saving afterwards - in a researcher specific folder.

def ica_label(dataset):
    global drive, savedir
    import mne
    import os
    from matplotlib import pyplot as plt
    plt.ion()

    # first try to access file containing drive and
    home=os.path.expanduser("~")
    file = "".join((home, '/', 'labeldir.txt'))
    drive = None
    savedir = None
    try:
        f=open(file, 'r')#with open(file) as f:
        for line in f:
            exec(line, globals())
        f.close()
        print(drive)
    except:
        print('SETTING UP THE DIRECTORIES')

    if drive is None:
        drive = int(input('Do you have access to mark`s (1) or kia`s (2) ohba drive?'))
        if drive==1:
            drive='mwoolrich'
        elif drive==2:
            drive='knobre'
        drive = "".join(('/ohba/pi/', drive, '/datasets/mrc_meguk/'))
        #drive = "".join(('/Volumes/T5_OHBA/', drive, '/datasets/mrc_meguk/'))
        # write to text file
        with open(file, "a") as text_file:
            print(f"drive = '{drive}'", file=text_file)

    if savedir is None:
        researcher_id = input('What are your initials?').lower()
        savedir = "".join((drive, researcher_id, '/'))
        with open(file, "a") as text_file:
            print(f"savedir = '{savedir}'", file=text_file)

    if not os.path.isdir(savedir):
        os.mkdir(savedir)

    print(f'### LABELING DATASET {dataset} ###')
    print('LOADING DATA')
    raw = mne.io.read_raw("".join((drive,dataset, '_raw.fif')))
    ica = mne.preprocessing.read_ica("".join((drive,dataset, '_ica.fif')))
    ica.exclude = [] # empty automatic labeling info
    print(ica.exclude)

    # copy ica to researcher specific folder
    print('COPYING DATA TO RESEARCHER SPECIFIC FOLDER')
    ica.save("".join((savedir, dataset, '_ica.fif')))

    # interactive components plot
    print('INTERACTIVE ICA LABELING')
    from osl_plot_ica import plot_ica
    plot_ica(ica,raw, block=True)
    plt.pause(0.1)

    print('SAVING DATA')
    ica.save("".join((savedir, dataset, '_ica.fif')))
    del ica, raw
    print(f'### LABELING DATASET {dataset} COMPLETE ###')

def main(argv=None):
    import argparse
    import sys

    if argv is None:
        argv = sys.argv[1:]
    print(argv)
    parser = argparse.ArgumentParser(description='Label ICA components.')
    parser.add_argument('dataset', type=str,
                        help='Name of the ICA dataset (from partnership data)')
    args = parser.parse_args(argv)
    ica_label(args.dataset)


if __name__ == '__main__':
    main()