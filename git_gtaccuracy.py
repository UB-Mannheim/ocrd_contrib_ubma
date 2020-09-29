# Find gt-text-files and compare them with other commits

import glob
import json
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

# OCReval need to be installed (https://github.com/eddieantonio/ocreval)
import click
import git  # gitpython
from tqdm import tqdm


@click.command()
@click.option('--globexpr', default="", required=True, help='Glob to search files.')
@click.option('-c', '--commit', default="", required=True, multiple=True,
              help='Commit to compare, if multiple times set exact these commits will be processed.')
@click.option('-n', '--count', default=-1, help='Commits range, default 1 (max-range -1).')
@click.option('--gitdir', default=".", help='Git directory.')
@click.option('--report', default="./report", help='Folder to the reports.')
@click.option('-v', '--verbose', count=True, help='Get more process information.')
def gtaccuracy_report(gitdir, globexpr, commit, count, report, verbose):
    fnames = glob.glob(globexpr)[:600]
    report = Path(report)

    if not report.joinpath("accuracy-reports/").exists():
        report.joinpath("accuracy-reports/").mkdir()

    repo = git.Repo(gitdir)
    accsum_report = None

    if len(commit) == 1:
        revlist = repo.git.execute(["git", "rev-list", "--reverse", f"{commit[0]}^1..HEAD"]).split("\n")[:count]
    else:
        revlist = commit

    res = defaultdict(list)

    for rev in revlist:
        print("Process commit: " + rev)
        if not fnames:
            break
        fnames_left = []
        for fname in tqdm(fnames):
            fname = Path(fname)
            try:
                old_text = repo.git.show(f"{rev}:{fname}")
            except Exception as exp:
                if verbose:
                    print(exp)
                fnames_left.append(fname)
                continue
            if old_text:
                res[rev].append((str(fname.absolute()), old_text))
                with tempfile.NamedTemporaryFile("w") as tmp:
                    tmp.write(old_text)
                    tmp.flush()
                    try:
                        subprocess.Popen(["accuracy", tmp.name, fname.absolute(),
                                          report.joinpath(f'accuracy-reports/{fname.name}').absolute()]).communicate()
                        if not accsum_report:
                            subprocess.Popen(['mv', report.joinpath(f'accuracy-reports/{fname.name}').absolute(),
                                              report.joinpath(f'Report')]).communicate()
                            accsum_report = report.joinpath(f'Report')
                        else:
                            # Version 1 (faster)
                            subprocess.Popen(["accsum", str(accsum_report),
                                              str(report.joinpath(f'accuracy-reports/{fname.name}').absolute())],
                                             stdout=report.joinpath(f'ReportTemp').open("w")).communicate()
                            subprocess.Popen(['mv', report.joinpath(f'ReportTemp').absolute(),
                                              report.joinpath(f'Report')]).communicate()
                            # Version 2 (cleaner)
                            # process = subprocess.Popen(["accsum", str(accsum_report), str(report.joinpath(f'accuracy-reports/{fname.name}').absolute())],stdout = subprocess.PIPE)
                            # stdout = process.communicate()
                            # accsum = open(report.joinpath(f'Accsum'),"wb")
                            # accsum.write(stdout[0])
                            # accsum.flush()
                            # accsum.close()
                    except Exception as exp:
                        if verbose:
                            print(exp)
                        continue
        else:
            fnames = fnames_left
    if verbose:
        print("Result of commits and matched files:\n")
        print(json.dumps(res, indent=4, ensure_ascii=False))
    with open(report.joinpath("results.json"), "w") as fout:
        json.dump(res, fout, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    gtaccuracy_report()
