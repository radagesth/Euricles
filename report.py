import os
import csv
from datetime import datetime

WIDTH = 66


def _line(char: str = "─") -> str:
    return char * WIDTH


def _center(text: str, fill: str = " ") -> str:
    return f"║{text.center(WIDTH)}{fill}║" if fill == " " else f"║{text.center(WIDTH, fill)}║"


def generate(results_by_profile: dict, output_dir: str = "output") -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"euricles_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)

    lines = []

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    n_profiles = len(results_by_profile)
    lines += [
        f"╔{'═' * WIDTH}╗",
        _center("EURICLES — REPORTE DE BÚSQUEDA DE EMPLEO"),
        _center(f"Fecha: {now_str}  |  Perfiles: {n_profiles}"),
        f"╚{'═' * WIDTH}╝",
        "",
    ]

    total_global = 0

    for profile_name, portal_results in results_by_profile.items():
        profile_total = sum(len(jobs) for jobs in portal_results.values())
        total_global += profile_total

        lines += [
            f"PERFIL: {profile_name}",
            "═" * WIDTH,
            "",
        ]

        for portal_name, jobs in portal_results.items():
            best_effort_note = " (best-effort)" if jobs and jobs[0].get("best_effort") else ""
            lines += [
                f"[ {portal_name} ] — {len(jobs)} resultado(s){best_effort_note}",
                _line("─"),
            ]

            if not jobs:
                lines.append("  Sin resultados para este portal.")
            else:
                for i, job in enumerate(jobs, 1):
                    lines.append(
                        f"{i:>2}. {job['title']} | {job['company']} | {job['location']} | {job['date']}"
                    )
                    if job["url"]:
                        lines.append(f"    {job['url']}")

            lines.append("")

        lines += [
            f"  SUBTOTAL PERFIL '{profile_name}': {profile_total} oferta(s)",
            "═" * WIDTH,
            "",
        ]

    lines += [
        "RESUMEN GLOBAL",
        _line("─"),
    ]
    for profile_name, portal_results in results_by_profile.items():
        count = sum(len(j) for j in portal_results.values())
        lines.append(f"  {profile_name:<40} {count:>4} oferta(s)")

    lines += [
        _line("─"),
        f"  {'TOTAL':<40} {total_global:>4} oferta(s)",
        "",
        f"  Archivo generado: {filepath}",
        "",
        f"╔{'═' * WIDTH}╗",
        _center("Búsqueda completada por EURICLES"),
        f"╚{'═' * WIDTH}╝",
    ]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    csv_path = filepath.replace(".txt", ".csv")
    try:
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["Perfil", "Portal", "Título", "Empresa", "Ubicación", "Fecha", "URL"])
            for profile_name, portal_results in results_by_profile.items():
                for portal_name, jobs in portal_results.items():
                    for job in jobs:
                        writer.writerow([
                            profile_name,
                            portal_name,
                            job.get("title", ""),
                            job.get("company", ""),
                            job.get("location", ""),
                            job.get("date", ""),
                            job.get("url", ""),
                        ])
    except Exception:
        pass

    return filepath
