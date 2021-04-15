import os
import psutil

from datetime import datetime, timedelta

from plotmanager.library.utilities.processes import get_manager_processes, get_chia_drives

def _get_row_info(pid, running_work):
    work = running_work[pid]
    phase_times = work.phase_times
    elapsed_time = (datetime.now() - work.datetime_start)
    elapsed_time = pretty_print_time(elapsed_time.seconds)
    row = [work.job.name if work.job else '?', pid, work.datetime_start.strftime('%Y-%m-%d %H:%M:%S'),
           elapsed_time, work.current_phase, phase_times.get(1, ''), phase_times.get(2, ''), phase_times.get(3, ''),
           phase_times.get(4, ''), work.progress]
    return [str(cell) for cell in row]


def pretty_print_bytes(size, size_type):
    if size_type.lower() == 'gb':
        power = 3
    elif size_type.lower() == 'tb':
        power = 4
    else:
        raise Exception('Failed to identify size_type.')
    return round(size / (1024 ** power), 2)


def pretty_print_time(seconds):
    total_minutes, second = divmod(seconds, 60)
    hour, minute = divmod(total_minutes, 60)
    return f"{hour:02}:{minute:02}:{second:02}"


def pretty_print_table(rows):
    max_characters = [0 for cell in rows[0]]
    for row in rows:
        for i, cell in enumerate(row):
            length = len(cell)
            if len(cell) <= max_characters[i]:
                continue
            max_characters[i] = length

    headers = "   ".join([cell.center(max_characters[i]) for i, cell in enumerate(rows[0])])
    separator = '=' * (sum(max_characters) + 3 * len(max_characters))
    console = [separator, headers, separator]
    for row in rows[1:]:
        console.append("   ".join([cell.ljust(max_characters[i]) for i, cell in enumerate(row)]))
    console.append(separator)
    return "\n".join(console)


def get_job_data(jobs, running_work):
    rows = []
    headers = ['num', 'job', 'pid', 'start', 'elapsed_time', 'current', 'phase1', 'phase2', 'phase3', 'phase4', 'progress']
    added_pids = []
    for job in jobs:
        for pid in job.running_work:
            if pid not in running_work:
                continue
            rows.append(_get_row_info(pid, running_work))
            added_pids.append(pid)
    for pid in running_work.keys():
        if pid in added_pids:
            continue
        rows.append(_get_row_info(pid, running_work))
        added_pids.append(pid)
    rows.sort(key=lambda x: (x[3]), reverse=True)
    for i in range(len(rows)):
        rows[i] = [str(i+1)] + rows[i]
    rows = [headers] + rows
    return pretty_print_table(rows)


def get_drive_data(drives):
    chia_drives = get_chia_drives()
    headers = ['type', 'drive', 'used', 'total', 'percent', 'plots']
    rows = [headers]
    for drive_type, drives in drives.items():
        for drive in drives:
            usage = psutil.disk_usage(drive)
            rows.append([drive_type, drive, f'{pretty_print_bytes(usage.used, "tb")}TB',
                         f'{pretty_print_bytes(usage.total, "tb")}TB', f'{usage.percent}%',
                         str(chia_drives[drive_type].get(drive, '?'))])
    return pretty_print_table(rows)


def print_view(jobs, running_work, analysis, drives, next_log_check):
    # Job Table
    job_data = get_job_data(jobs=jobs, running_work=running_work)

    # Drive Table
    drive_data = get_drive_data(drives)

    manager_processes = get_manager_processes()

    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
    print(job_data)
    print(f'Manager Status: {"Running" if manager_processes else "Stopped"}')
    print()
    print(drive_data)
    print(f'CPU Usage: {psutil.cpu_percent()}%')
    ram_usage = psutil.virtual_memory()
    print(f'RAM Usage: {pretty_print_bytes(ram_usage.used, "gb")}/{pretty_print_bytes(ram_usage.total, "gb")}GB '
          f'({ram_usage.percent}%)')
    print()
    print(f'Plots Completed Yesterday: {analysis["summary"].get(datetime.now().date() - timedelta(days=1), 0)}')
    print(f'Plots Completed Today: {analysis["summary"].get(datetime.now().date(), 0)}')
    print()
    print(f"Next log check at {next_log_check.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
