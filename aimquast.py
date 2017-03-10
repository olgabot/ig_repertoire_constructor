#!/usr/bin/env python2

import sys
import matplotlib
matplotlib.use('Agg')
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
igrec_dir = current_dir
sys.path.append(igrec_dir + "/src/extra/ash_python_utils/")
from ash_python_utils import CreateLogger, AttachFileLogger, mkdir_p

sys.path.append(igrec_dir + "/py")

from aimquast_impl import Report, reconstruct_rcm, write_rcm, run_consensus_constructor, Repertoire, RepertoireMatch, RcmVsRcm
from aimquast_impl import splittering


def parse_command_line(description="aimQUAST"):
    import argparse

    def ActionTestFactory(name):
        initial_reads = igrec_dir + "/aimquast_test_dataset/%s/input_reads.fa.gz" % name
        import os.path
        if not os.path.isfile(initial_reads):
            return None

        class ActionTest(argparse.Action):

            def __init__(self, option_strings, dest, nargs=None, **kwargs):
                super(ActionTest, self).__init__(option_strings, dest, nargs=0, **kwargs)

            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, "initial_reads", initial_reads)
                setattr(namespace, "output_dir", "aimquast_test_%s" % name)
                setattr(namespace, "constructed_repertoire", igrec_dir + "/aimquast_test_dataset/%s/igrec/final_repertoire.fa.gz" % name)
                setattr(namespace, "constructed_rcm", igrec_dir + "/aimquast_test_dataset/%s/igrec/final_repertoire.rcm" % name)
                setattr(namespace, "reference_repertoire", igrec_dir + "/aimquast_test_dataset/%s/repertoire.fa.gz" % name)
                setattr(namespace, "reference_rcm", igrec_dir + "/aimquast_test_dataset/%s/repertoire.rcm" % name)

        return ActionTest

    parser = argparse.ArgumentParser(description=description)

    def add_test(name, key=None, display_name=None):
        if key is None:
            key = "--test-" + name
        if display_name is None:
            display_name = name

        test_action = ActionTestFactory(name)
        if test_action is not None:  # Test dataset exists
            parser.add_argument(key,
                                action=test_action,
                                help="Running on %s dataset" % display_name)

    add_test("test", key="--test")
    add_test("age1")
    add_test("age3")
    add_test("flu")
    add_test("presentation")

    parser.add_argument("--initial-reads", "-s",
                        type=str,
                        default="",
                        help="FASTA/FASTQ file with initial reads, empty string for non-providing (default: <empty>)")
    parser.add_argument("--constructed-repertoire", "-c",
                        type=str,
                        default="",
                        help="constructed repertoire file")
    parser.add_argument("--constructed-rcm", "-C",
                        type=str,
                        default="",
                        help="constructed RCM file, empty string for non-providing (default: <empty>)")
    parser.add_argument("--reference-repertoire", "-r",
                        type=str,
                        default="",
                        help="reference reperoire file, empty string for non-providing (default: <empty>)")
    parser.add_argument("--reference-rcm", "-R",
                        type=str,
                        default="",
                        help="reference repertoire RCM, empty for non-providing (default: <empty>)")
    parser.add_argument("--output-dir", "-o",
                        type=str,
                        help="output dir for results")
    parser.add_argument("--tau",
                        type=int,
                        default=6,
                        help="maximal distance for repertoire-to-repertoire matching (default: %(default)d)")
    parser.add_argument("--rcm-based",
                        action="store_true",
                        dest="rcm_based",
                        help="enable partition-based metrics and plots")
    parser.add_argument("--no-rcm-based",
                        action="store_false",
                        dest="rcm_based",
                        help="disable partition-based metrics and plots (default)")
    parser.set_defaults(rcm_based=False)
    parser.add_argument("--reference-size-cutoff",
                        default=5,
                        help="reference size cutoff (default: %(default)d)")
    parser.add_argument("--json",
                        help="file for JSON output (default: <output_dir>/aimquast.json)")
    parser.add_argument("--text",
                        help="file for text output (default: <output_dir>/aimquast.txt)")
    parser.add_argument("--export-bad-clusters",
                        action="store_true",
                        help="export bad clusters during reference-free analysis")
    parser.add_argument("--figure-format", "-F",
                        type=str,
                        default="svg,png,pdf",
                        help="format(s) for producing figures, empty for non-producing (default: %(default)s)")

    parser.add_argument("--no-reference-free",
                        dest="reference_free",
                        action="store_false",
                        help="disable reference-free metrics (default)")
    parser.add_argument("--reference-free",
                        dest="reference_free",
                        action="store_true",
                        help="enable reference-free metrics")
    parser.set_defaults(reference_free=False)

    parser.add_argument("--no-experimental",
                        dest="experimental",
                        action="store_false",
                        help="disable experimental features (default)")
    parser.add_argument("--experimental",
                        dest="experimental",
                        action="store_true",
                        help="enable experimental features")
    parser.set_defaults(experimental=False)

    args = parser.parse_args()

    args.reference_trash_cutoff = args.reference_trust_cutoff = args.reference_size_cutoff
    assert 0 < args.reference_trash_cutoff <= args.reference_trust_cutoff

    if args.output_dir is None:
        parser.print_help()
        sys.exit(1)

    args.log = args.output_dir + "/aimquast.log"

    if args.json is None:
        args.json = args.output_dir + "/aimquast.json"

    if args.text is None:
        args.text = args.output_dir + "/aimquast.txt"

    if args.reference_free:
        args.rcm_based = True

    args.reference_free_dir = args.output_dir + "/reference_free"
    args.reference_based_dir = args.output_dir + "/reference_based"

    args.figure_format = [fmt.strip() for fmt in args.figure_format.strip().split(",")]
    args.figure_format = [fmt for fmt in args.figure_format if fmt in ["svg", "pdf", "png"]]

    return args


def main(args):
    report = Report()

    if args.initial_reads and args.constructed_repertoire and not args.constructed_rcm:
        log.info("Try to reconstruct repertoire RCM file...")
        rcm = reconstruct_rcm(args.initial_reads, args.constructed_repertoire)
        args.constructed_rcm = args.output_dir + "/constructed.rcm"
        write_rcm(rcm, args.constructed_rcm)

    if args.initial_reads and not args.constructed_repertoire and args.constructed_rcm:
        log.info("Try to reconstruct repertoire sequence file...")
        args.constructed_repertoire = args.output_dir + "/constructed.fa.gz"
        run_consensus_constructor(rcm_file=args.constructed_rcm,
                                  initial_reads=args.initial_reads,
                                  output_file=args.constructed_repertoire)

    if args.initial_reads and args.reference_repertoire and not args.reference_rcm and args.rcm_based:
        log.info("Try to reconstruct reference RCM file...")
        rcm = reconstruct_rcm(args.initial_reads, args.reference_repertoire)
        args.reference_rcm = args.output_dir + "/reference.rcm"
        write_rcm(rcm, args.reference_rcm)

    if args.initial_reads and not args.reference_repertoire and args.reference_rcm and args.rcm_based:
        log.info("Try to reconstruct reference repertoire sequence file...")
        args.reference_repertoire = args.output_dir + "/reference.fa.gz"
        run_consensus_constructor(rcm_file=args.reference_rcm,
                                  initial_reads=args.initial_reads,
                                  output_file=args.reference_repertoire)

    if args.initial_reads and args.constructed_repertoire and args.constructed_rcm and args.rcm_based:
        rep = Repertoire(args.constructed_rcm, args.initial_reads, args.constructed_repertoire)

    def ref_free_plots(rep, name, dir):
        if args.figure_format:
            mkdir_p(dir)

            rep.plot_distribution_of_errors_in_reads(out=dir + "/%s_distribution_of_errors_in_reads" % name,
                                                     format=args.figure_format)
            rep.plot_estimation_of_max_error_distribution(out=dir + "/%s_estimation_of_max_error_distribution" % name,
                                                          format=args.figure_format)
            for i in range(5):
                cluster = rep.largest(i)
                cluster.plot_profile(out=dir + "/%s_cluster_discordance_profile_largest_%d" % (name, i + 1),
                                     format=args.figure_format)
                cluster.plot_profile(out=dir + "/%s_cluster_error_profile_largest_%d" % (name, i + 1),
                                     discordance=False,
                                     format=args.figure_format)

            rep.plot_profile(out=dir + "/%s_cluster_discordance_profile" % name,
                             format=args.figure_format)
            rep.plot_profile(out=dir + "/%s_cluster_error_profile" % name,
                             discordance=False,
                             format=args.figure_format)

        if args.export_bad_clusters:
            mkdir_p(dir)
            rep.export_bad_clusters(out=dir + "/bad_%s_clusters/" % name)
        rep.report(report, "%s_stats" % name)

    if args.initial_reads and args.constructed_repertoire and args.constructed_rcm and args.reference_free and args.rcm_based:
        ref_free_plots(rep, "constructed", args.reference_free_dir)

    if args.initial_reads and args.reference_repertoire and args.reference_rcm and args.reference_free and args.rcm_based:
        rep_ideal = Repertoire(args.reference_rcm, args.initial_reads, args.reference_repertoire)
        ref_free_plots(rep_ideal, "reference", args.reference_free_dir)

    if args.constructed_repertoire and args.reference_repertoire:
        res = RepertoireMatch(args.constructed_repertoire,
                              args.reference_repertoire,
                              tmp_file=None,
                              max_tau=args.tau,
                              reference_trash_cutoff=args.reference_trash_cutoff,
                              reference_trust_cutoff=args.reference_trust_cutoff,
                              log=log)

        res.report(report)

        if args.figure_format:
            mkdir_p(args.reference_based_dir)

            for size in [1, 3, 5, 10]:
                res.plot_sensitivity_precision(what="ref2cons",
                                               out=args.reference_based_dir + "/reference_to_constructed_distance_distribution_size_%d" % size,
                                               size=size, differential=True,
                                               format=args.figure_format)

                res.plot_sensitivity_precision(what="cons2ref",
                                               out=args.reference_based_dir + "/constructed_to_reference_distance_distribution_size_%d" % size,
                                               size=size, differential=True,
                                               format=args.figure_format)

                res.plot_octoplot(out=args.reference_based_dir + "/octoplot",
                                  format=args.figure_format)

            res.plot_min_cluster_size_choose(out=args.reference_based_dir + "/min_cluster_size_choose",
                                             format=args.figure_format)

            res.plot_error_pos_dist(out=args.reference_based_dir + "/error_pos_dist",
                                    format=args.figure_format)

            res.plot_reference_vs_constructed_size(out=args.reference_based_dir + "/reference_vs_constructed_size",
                                                   format=args.figure_format, marginals=False)

            if args.experimental:
                res.plot_reference_vs_constructed_size(out=args.reference_based_dir + "/reference_vs_constructed_size_hexes",
                                                       points=False,
                                                       format=args.figure_format, marginals=False)

            res.plot_multiplicity_distributions(out=args.reference_based_dir + "/multiplicity_distribution",
                                                format=args.figure_format)

    if args.constructed_rcm and args.reference_rcm and args.rcm_based:
        rcm2rcm = RcmVsRcm(args.constructed_rcm,
                           args.reference_rcm)

        rcm2rcm.report(report, "rcm_stats_all_clusters")

        size = args.reference_size_cutoff

        rcm2rcm_large = rcm2rcm.prune_copy(size, 1)

        # TODO fix report!!!!????
        rcm2rcm_large.report(report)

        if args.figure_format:
            mkdir_p(args.reference_based_dir)
            rcm2rcm.plot_majority_secondary(out=args.reference_based_dir + "/constructed_majority_secondary", format=args.figure_format)
            rcm2rcm.plot_size_nomajority(out=args.reference_based_dir + "/constructed_size_nomajority", format=args.figure_format)
            rcm2rcm.plot_purity_distribution(out=args.reference_based_dir + "/constructed_purity_distribution", format=args.figure_format)
            rcm2rcm.plot_purity_distribution(out=args.reference_based_dir + "/constructed_purity_distribution_ylog", format=args.figure_format, ylog=True)
            rcm2rcm.plot_discordance_distribution(out=args.reference_based_dir + "/constructed_discordance_distribution", format=args.figure_format)
            rcm2rcm.plot_discordance_distribution(out=args.reference_based_dir + "/constructed_discordance_distribution_ylog", format=args.figure_format, ylog=True)

            rcm2rcm.plot_majority_secondary(out=args.reference_based_dir + "/reference_majority_secondary", format=args.figure_format, constructed=False)
            rcm2rcm.plot_size_nomajority(out=args.reference_based_dir + "/reference_size_nomajority", format=args.figure_format, constructed=False)
            rcm2rcm.plot_purity_distribution(out=args.reference_based_dir + "/reference_purity_distribution", format=args.figure_format, constructed=False)
            rcm2rcm.plot_purity_distribution(out=args.reference_based_dir + "/reference_purity_distribution_ylog", format=args.figure_format, constructed=False, ylog=True)
            rcm2rcm.plot_discordance_distribution(out=args.reference_based_dir + "/reference_discordance_distribution", format=args.figure_format, constructed=False)
            rcm2rcm.plot_discordance_distribution(out=args.reference_based_dir + "/reference_discordance_distribution_ylog", format=args.figure_format, constructed=False, ylog=True)

            rcm2rcm_large.plot_majority_secondary(out=args.reference_based_dir + "/constructed_majority_secondary_large", format=args.figure_format)
            rcm2rcm_large.plot_size_nomajority(out=args.reference_based_dir + "/constructed_size_nomajority_large", format=args.figure_format)
            rcm2rcm_large.plot_purity_distribution(out=args.reference_based_dir + "/constructed_purity_distribution_large", format=args.figure_format)
            rcm2rcm_large.plot_purity_distribution(out=args.reference_based_dir + "/constructed_purity_distribution_large_ylog", format=args.figure_format, ylog=True)
            rcm2rcm_large.plot_discordance_distribution(out=args.reference_based_dir + "/constructed_discordance_distribution_large", format=args.figure_format)
            rcm2rcm_large.plot_discordance_distribution(out=args.reference_based_dir + "/constructed_discordance_distribution_large_ylog", format=args.figure_format, ylog=True)

            rcm2rcm_large.plot_majority_secondary(out=args.reference_based_dir + "/reference_majority_secondary_large", format=args.figure_format, constructed=False)
            rcm2rcm_large.plot_size_nomajority(out=args.reference_based_dir + "/reference_size_nomajority_large", format=args.figure_format, constructed=False)
            rcm2rcm_large.plot_purity_distribution(out=args.reference_based_dir + "/reference_purity_distribution_large", format=args.figure_format, constructed=False)
            rcm2rcm_large.plot_purity_distribution(out=args.reference_based_dir + "/reference_purity_distribution_large_ylog", format=args.figure_format, constructed=False, ylog=True)
            rcm2rcm_large.plot_discordance_distribution(out=args.reference_based_dir + "/reference_discordance_distribution_large", format=args.figure_format, constructed=False)
            rcm2rcm_large.plot_discordance_distribution(out=args.reference_based_dir + "/reference_discordance_distribution_large_ylog", format=args.figure_format, constructed=False, ylog=True)

    if args.constructed_rcm and args.reference_rcm and args.rcm_based and args.constructed_repertoire and args.reference_repertoire and args.experimental:
        splittering(rcm2rcm, rep, args, report)

    log.info(report)

    if args.text:
        report.toText(args.text)

    if args.json:
        report.toJson(args.json)


def SupportInfo(log):
    log.info("\nIn case you have troubles running aimQUAST, "
             "you can write to igtools_support@googlegroups.com.")
    log.info("Please provide us with aimquast.log file from the output directory.")

if __name__ == "__main__":
    args = parse_command_line()
    mkdir_p(args.output_dir)
    log = CreateLogger("aimQUAST")
    if args.log:
        AttachFileLogger(log, args.log)

    try:
        log.info("Command line: %s" % " ".join(sys.argv))
        main(args)
        log.info("\nThank you for using aimQUAST!")
    except (KeyboardInterrupt):
        log.info("\naimQUAST was interrupted!")
    except Exception:
        exc_type, exc_value, _ = sys.exc_info()
        if exc_type == SystemExit:
            sys.exit(exc_value)
        else:
            log.exception(exc_value)
            log.info("\nERROR: Exception caught.")
            SupportInfo(log)
            sys.exit(exc_value)
    except BaseException:
        exc_type, exc_value, _ = sys.exc_info()
        if exc_type == SystemExit:
            sys.exit(exc_value)
        else:
            log.exception(exc_value)
            log.info("\nERROR: Exception caught.")
            SupportInfo(log)
            sys.exit(exc_value)

    log.info("Log was written to " + args.log)
