#!/usr/bin/env python
"""Analyze the parallel efficiency of the MPI-FFT algorithsm in in the GS part.
Use paral_kgb=1 and fftalg_list = [312, 402, 401]"""
from __future__ import division, print_function, unicode_literals, absolute_import

import sys
import abipy.abilab as abilab
import abipy.data as abidata

from abipy.benchmarks import bench_main, BenchmarkFlow


def make_input(paw=False):
    """
    Build and return an input file for GS calculations with paral_kgb=1
    """
    pseudos = abidata.pseudos("14si.pspnc", "8o.pspnc") if not paw else \
              abidata.pseudos("Si.GGA_PBE-JTH-paw.xml", "o.paw")

    structure = abidata.structure_from_ucell("SiO2-alpha")

    inp = abilab.AbinitInput(structure, pseudos)
    inp.set_kmesh(ngkpt=[1,1,1], shiftk=[0,0,0])

    # Global variables
    ecut = 24
    inp.set_vars(
        ecut=ecut,
        pawecutdg=ecut*2 if paw else None,
        paral_kgb=1,
        nsppol=1,
        nband=28,
        npkpt=1,
        npband=1,
        npfft=1,
        fftalg=112,
        #istwfk="*1",
        timopt=-1,
        chksymbreak=0,
        prtwf=0,
        prtden=0,
        tolvrs=1e-8,
        nstep=10,
    )

    return inp


def build_flow(options):
    fftalg_list = [312, 402, 401]
    ecut_list = list(range(200, 610, 100)) 
    ecut_list = [400,]

    if options.mpi_list is None: mpi_list = [2, 4, 6, 8]
    print("Using mpi_list:", mpi_list)

    template = make_input()
    flow = BenchmarkFlow(workdir=options.get_workdir(__file__), remove=options.remove)

    omp_threads = 1
    for fftalg in fftalg_list: 
        work = abilab.Work()
        for npfft in mpi_list:
            if not options.accept_mpi_omp(npfft, omp_threads): continue
            manager = options.manager.new_with_fixed_mpi_omp(npfft, omp_threads)
            for inp in abilab.input_gen(template, fftalg=fftalg, npfft=npfft, ecut=ecut_list):
                work.register_scf_task(inp, manager=manager)
        flow.register_work(work)

    return flow.allocate()


@bench_main
def main(options):
    if options.info:
        # print doc string and exit.
        print(__doc__)
        return 

    flow = build_flow(options)
    flow.build_and_pickle_dump()
    return flow


if __name__ == "__main__":
    sys.exit(main())
