import argparse
import ROOT
from array import array

def getListofRootfiles(rfs):
    # Prepare list of rootfiles from command line argument
    rootfiles = []
    if rfs:
        rootfiles = rfs.split(',')
        if len(rootfiles) > 1:
            print("-"*50)
            print("Merging these root files in the order they are listed: \n\t", rootfiles)
        else:
            raise ValueError('Only one rootfile passed to merger script. No need to merge')
    else:
        raise ValueError('No rootfiles to merge. Please pass a list of root files to the "-f" option')
    return rootfiles

def getListofTrees(rootfiles, treeName, listOfFiles):
    trees = [None]*len(rootfiles)
    for i, rf in enumerate(rootfiles):
        listOfFiles[i] = ROOT.TFile.Open(rf, "READ")
        t = listOfFiles[i].Get(treeName)
        trees[i] = t
    return trees

def getBranchInfo(b):
    name = b.GetName()
    title = b.GetTitle()
    rootType = None
    length = b.GetListOfLeaves().UncheckedAt(0).GetLen()

    try:
        currentClass = b.GetCurrentClass()
        rootType = currentClass.GetName()
    except:
        rootType = title.replace(name,"")

    return name, title, rootType, length

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser("usage: %prog [options]\n")
    parser.add_argument('-f', dest='rootfiles', type=str, default = '', help = "Lists of root files to merge, comma separated")
    options = parser.parse_args()
    workingArea = "/uscms/home/cmadrid/nobackup/ana/SensorBeam2022/TestbeamReco/test/tmp"
    outputFileName = "output.root"
    nScopeChannels = 8
    treeName = "pulse"

    # Get trees from input root files
    rootfiles = getListofRootfiles(options.rootfiles)
    nMergeChannels = len(rootfiles)*nScopeChannels
    listOfFiles = [ROOT.TFile for i in range(len(options.rootfiles))]
    trees = getListofTrees(rootfiles, treeName, listOfFiles)

    # Figure out which branches need to be copied and which need to be merged
    lob = trees[0].GetListOfBranches()
    next = ROOT.TIter(lob)
    vars = {}
    for i in range(0, len(lob)):
        branch = next()
        name, title, rootType, length = getBranchInfo(branch)
        vars[name] = {"name":name, "title":title, "type":rootType, "length":length}
        if "[{}]".format(nScopeChannels) in rootType:
            vars[name]["doMerge"] = True
        else:
            vars[name]["doMerge"] = False

    # Copy the branches that do not need to be merged and mark merge branches for removal
    outputFile = ROOT.TFile(outputFileName,"RECREATE")
    print("-"*50)
    print("Copying constant variables from all root files...")
    tmpTree = trees[0].CopyTree("")
    for var, info in vars.items():
        if info["doMerge"]:   
            tmpTree.SetBranchStatus(var, 0)
    outputTree = tmpTree.CopyTree("")

    # Redefine merge branches 
    for var, info in vars.items():
        if info["doMerge"]:
            info["array"] = array("f", [0]*nMergeChannels*info["length"]) #Bad Hardcode here: Assuming all merged branches are floats arrays
            newType = info["type"].replace("[{}]".format(nScopeChannels), "[{}]".format(nMergeChannels))
            info["branch"] = outputTree.Branch(var, info["array"], '{}{}'.format(var,newType))

    # Fill values for the merge branches from all of the input root files
    print("-"*50)
    print("Merging scope based variables")
    print("-"*50)
    for ienv, entry in enumerate(outputTree):
        if ienv % 1000 == 0: print(ienv)
        for t in trees:
            t.GetEntry(ienv)

        for var, info in vars.items():
            if info["doMerge"]:
                for i in range(len(trees)):
                    v = getattr(trees[i], var)
                    for j in range(len(v)):
                        info["array"][j + i*len(v)] = v[j]
                info["branch"].Fill()

    # Write it all out and call it a day
    outputTree.Write()
    outputFile.Close()

if __name__ == '__main__':   
    main()
    