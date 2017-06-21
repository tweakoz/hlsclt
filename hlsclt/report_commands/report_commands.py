# -*- coding: utf-8 -*-
""" Report subcommands for HLSCLT.

Copyright (c) 2017 Ben Marshall
"""

### Imports ###
import click
import os
import subprocess
from glob import glob
from hlsclt.helper_funcs import just_loop_on, find_solution_num

### Supporting Functions ###
# Function to check if project exists
def check_for_project(ctx):
    config = ctx.obj.config
    if not glob(config["project_name"]):
        click.echo("Error: Can't find a project folder have you run a build process yet?")
        raise click.Abort()

# Function for opening reports.
def open_report(ctx,report):
    config = ctx.obj.config
    solution_num = ctx.obj.solution_num
    report_files = []
    if report == 'csim':
        report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/csim/report/" + config["top_level_function_name"] + "_csim.log")
    elif report == 'syn':
        report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/syn/report/" + config["top_level_function_name"] + "_csynth.rpt")
    elif report == 'cosim':
        report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/sim/report/" + config["top_level_function_name"] + "_cosim.rpt")
        for language in just_loop_on(config["language"]):
            report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/sim/report/" + language + "/" + config["top_level_function_name"] + ".log")
    elif report == 'export':
        for language in just_loop_on(config["language"]):
            report_files.append(config["project_name"] + "/solution" + str(solution_num) + "/impl/report/" + language + "/" + config["top_level_function_name"] + "_export.rpt")
    for file in report_files:
        return_val = os.system('xdg-open ' + file + ' >/dev/null 2>&1')
        if return_val != 0:
            click.echo("Error: Looks like the " + report + " report doesn't exist for project: " + config["project_name"] + ", solution number: " + str(solution_num) + ". Make sure you have run that build stage.")

# Function for opening the HLS GUI
def open_project_in_gui(ctx):
    config = ctx.obj.config
    hls_process = subprocess.Popen(["vivado_hls", "-p", config["project_name"]])

# Function for finding the project status
def gather_project_status(ctx):
    config = ctx.obj.config
    solution_num = ctx.obj.solution_num
    project_status = []
    if os.path.isfile(config["project_name"] + "/solution" + str(solution_num) + "/csim/report/" + config["top_level_function_name"] + "_csim.log"):
        project_status.append("csim_done")
    if os.path.isfile(config["project_name"] + "/solution" + str(solution_num) + "/syn/report/" + config["top_level_function_name"] + "_csynth.rpt"):
        project_status.append('syn_done')
    if os.path.isfile(config["project_name"] + "/solution" + str(solution_num) + "/sim/report/" + config["top_level_function_name"] + "_cosim.rpt"):
        project_status.append('cosim_done')
        with click.open_file(config["project_name"] + "/solution" + str(solution_num) + "/sim/report/" + config["top_level_function_name"] + "_cosim.rpt") as f:
            for line in f:
                if "vhdl" in line.lower():
                    if "pass" in line.lower():
                        project_status.append('cosim_vhdl_pass')
                    elif "fail" in line.lower():
                        project_status.append('cosim_vhdl_fail')
                if "verilog" in line.lower():
                    if "pass" in line.lower():
                        project_status.append('cosim_verilog_pass')
                    elif "fail" in line.lower():
                        project_status.append('cosim_verilog_fail')
    if os.path.isdir(config["project_name"] + "/solution" + str(solution_num) + "/impl/ip"):
        project_status.append('export_ip_done')
    if os.path.isdir(config["project_name"] + "/solution" + str(solution_num) + "/impl/sysgen"):
        project_status.append('export_sysgen_done')
    for language in just_loop_on(config["language"]):
        if os.path.isfile(config["project_name"] + "/solution" + str(solution_num) + "/impl/report/" + language + "/" + config["top_level_function_name"] + "_export.rpt"):
            if language == "vhdl":
                project_status.append('evaluate_vhdl_done')
            elif language == "verilog":
                project_status.append('evaluate_verilog_done')
    return project_status


# Function for printing out the project status
def print_project_status(ctx):
    project_status = gather_project_status(ctx)
    click.echo(project_status)


### Click Command Definitions ###
# Report Command
@click.command('report', short_help='Open reports.')
@click.option('-s', '--stage', required=True, multiple=True,
                type=click.Choice(['csim','syn','cosim','export']),
                help='Which build stage to open the report for. Multiple occurances accepted')
@click.pass_context
def report(ctx,stage):
    """Opens the Vivado HLS report for the chosen build stages."""
    check_for_project(ctx)
    ctx.obj.solution_num = find_solution_num(ctx)
    for report in stage:
        open_report(ctx,report)

@click.command('open_gui', short_help='Open the Vivado HLS GUI and load the project.')
@click.pass_context
def open_gui(ctx):
    """Opens the Vivado HLS GUI and loads the project."""
    check_for_project(ctx)
    open_project_in_gui(ctx)

@click.command('status', short_help='Print out the current project status.')
@click.pass_context
def status(ctx):
    """Prints out a message detailing the current project status."""
    check_for_project(ctx)
    ctx.obj.solution_num = find_solution_num(ctx)
    print_project_status(ctx)
