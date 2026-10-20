    p_loc.add_argument("--profile-file", dest="profile_file", metavar="FILE",
                       help="JSON/YAML profile file for locale-aware generation")
    p_loc.add_argument("-o", "--output", help="Output file")

    p_pbmp = sub.add_parser(
        "pbmp",
        help="Full PBMP strategy distribution for a profile",
        description=(
            "Print weighted engine plan (History/Context/Behavior/Population).\n\n"
            "Examples:\n"
            "  wlf.py pbmp --n-engines 8\n"
            "  wlf.py pbmp --profile-file alvo.yaml"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_pbmp.add_argument("--profile-file", dest="profile_file", metavar="FILE",
                        help="JSON/YAML profile")
    p_pbmp.add_argument("--n-engines", dest="n_engines", type=int, default=5,
                        help="Top strategies to show (default: 5)")

    p_evl = sub.add_parser(
        "evolve",
        help="Evolutionary generation (genetic / MAP-Elites)",
        description=(
            "Population-based candidate search.\n\n"
            "Examples:\n"
            "  wlf.py --limit 2000 evolve --mode genetic -o ga.lst\n"
            "  wlf.py evolve --mode map-elites --seed-file seeds.txt --limit 5000"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_evl.add_argument("--mode", choices=["genetic", "map-elites"], default="genetic")
    p_evl.add_argument("--seed-file", dest="seed_file", metavar="FILE",
                       help="Seed wordlist to initialize population")
    p_evl.add_argument("-o", "--output", help="Output file")

    p_ge = sub.add_parser(
        "graph-expand",
        help="Graph neighbourhood expansion from a seed corpus",
        description=(
            "Expand transformations around seed passwords.\n\n"
            "Examples:\n"
            "  wlf.py --limit 5000 graph-expand seeds.txt -o graph.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_ge.add_argument("corpus_file", metavar="CORPUS", help="Seed corpus file")
    p_ge.add_argument("-o", "--output", help="Output file")

    p_tm = sub.add_parser(
        "temporal-model",
        help="Temporal drift generation across years",
        description=(
            "Evolve seed styles from base_year toward target_year.\n\n"
            "Examples:\n"
            "  wlf.py temporal-model --seed-file seeds.txt --base-year 2019 --target-year 2026"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_tm.add_argument("--seed-file", dest="seed_file", metavar="FILE")
    p_tm.add_argument("--base-year", dest="base_year", type=int, default=2019)
    p_tm.add_argument("--target-year", dest="target_year", type=int, default=2026)
    p_tm.add_argument("-o", "--output", help="Output file")

    p_dpc = sub.add_parser(
        "domain-pcfg",
        help="Domain-specific PCFG (corporate/healthcare/finance/...)",
        description=(
            "Sector-biased PCFG-style expansion.\n\n"
            "Examples:\n"
            "  wlf.py --limit 5000 domain-pcfg --sector healthcare -o hc.lst\n"
            "  wlf.py domain-pcfg --sector finance --corpus-file corp.txt"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_dpc.add_argument(
        "--sector",
        default="generic",
        help="Sector label (default: generic)",
    )
    p_dpc.add_argument("--corpus-file", dest="corpus_file", metavar="FILE",
                       help="Optional domain corpus for terminals")
    p_dpc.add_argument("-o", "--output", help="Output file")

    p_plg = sub.add_parser(
        "plugin",
        help="List/run user plugins (~/.wlf/plugins/)",
        description=(
            "Plugin discovery and execution.\n\n"
            "Examples:\n"
            "  wlf.py plugin list\n"
            "  wlf.py --limit 1000 plugin run myplugin -o plug.lst"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_plg.add_argument(
        "plugin_sub", nargs="?", default="list", choices=["list", "run"],
        help="Sub-command (default: list)",
    )
    p_plg.add_argument("plugin_name", nargs="?", default=None,
                       help="Plugin name for run")
    p_plg.add_argument("-o", "--output", help="Output file when running a plugin")

    p_vi = sub.add_parser(
        "vae-interp",
        help="VAE latent-space interpolation between two passwords",
        description=(
            "Requires optional [gpu]/neural] torch stack when using real VAE weights.\n\n"
            "Examples:\n"
            "  wlf.py vae-interp senha1 senha2 --steps 10"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_vi.add_argument("pw_from", help="Start password")
    p_vi.add_argument("pw_to", help="End password")
    p_vi.add_argument("--steps", type=int, default=10, help="Interpolation steps")
    p_vi.add_argument("-o", "--output", help="Output file")

    # ── test (credential testing pipeline) ──────────────────────────────────
    p_te = sub.add_parser(
        "test",
        help="Credential testing: generate wordlist + hashcat cracking",
        description=(
            "Generate a targeted wordlist and test it against a hash file.\n\n"
            "Examples:\n"
            "  wlf.py test --target hashes.txt\n"
            "  wlf.py test --target hashes.txt --model M2 --mode ntlm\n"
            "  wlf.py test --target hashes.txt --max-words 500000 --timeout 600"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_te.add_argument("--target", "-t", required=True, help="Hash file to crack")
    p_te.add_argument("--model", default="M2", help="Generation model (default: M2)")
    p_te.add_argument("--mode", help="Hash mode name or number (auto-detect if omitted)")
    p_te.add_argument("--max-words", dest="max_words", type=int, default=100000,
                      help="Max wordlist size (default: 100000)")
    p_te.add_argument("--timeout", type=int, default=300,
                      help="Hashcat timeout in seconds (default: 300)")
    p_te.add_argument("-o", "--output", default=".", help="Output directory for report")

    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    return parser


# ── Entrypoint ────────────────────────────────────────────────────────────────

