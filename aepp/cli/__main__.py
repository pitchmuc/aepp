import aepp
from aepp import synchronizer, schema, schemamanager, fieldgroupmanager, datatypemanager, identity, queryservice,catalog,flowservice,sandboxes, segmentation, customerprofile, knowledgegraph, deletion
from aepp.cli.upsfieldsanalyzer import UpsFieldsAnalyzer
import argparse, cmd, shlex, json
from functools import wraps
from rich.console import Console
from rich import box
from rich.bar import Bar
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from pathlib import Path
from io import FileIO
import pandas as pd
from datetime import datetime, timezone, timedelta
import urllib.parse
from typing import Any, Concatenate, ParamSpec, ParamSpecKwargs
from collections.abc import Callable
import os
from math import isfinite

P = ParamSpec("P")

# --- 1. The Decorator (The Gatekeeper) ---
def login_required(f:Callable[Concatenate["ServiceShell", P], None]) -> Callable[Concatenate["ServiceShell", P], None]:
    """Decorator to block commands if not logged in."""
    @wraps(f)
    def wrapper(self:"ServiceShell", *args:P.args, **kwargs:P.kwargs) -> None:
        if not hasattr(self, 'config') or self.config is None:
            print("(!) Access Denied: You must setup config first.")
            return
        return f(self, *args, **kwargs)
    return wrapper

def clear_terminal():
    """Clears the terminal screen based on the OS."""
    # os.name is 'nt' for Windows, 'posix' for Mac/Linux
    os.system('cls' if os.name == 'nt' else 'clear')

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

class ParseDict(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        d = getattr(namespace, self.dest) or {}
        for item in values:
            try:
                k, v = item.split('=', 1)
                d[k] = v
            except ValueError:
                raise argparse.ArgumentError(self, f"Could not parse geometry '{item}'. Must be in key=value format.")
        setattr(namespace, self.dest, d)

console = Console()

# --- 2. The Interactive Shell ---
class ServiceShell(cmd.Cmd):
    def __init__(self, **kwargs:ParamSpecKwargs) -> None:
        super().__init__()
        self.config = None
        self.connectInstance = True
        self.ups_profile_analyzer:UpsFieldsAnalyzer|None = None
        self.graph = None
        if kwargs.get("config_file") is not None:
            config_path = Path(kwargs.get("config_file"))
            if not config_path.is_absolute():
                config_path = Path.cwd() / config_path
        if kwargs.get("config_file") is not None:
            dict_config = json.load(FileIO(config_path))
            if kwargs.get("sandbox") is None:
                self.sandbox = str(dict_config.get("sandbox-name","prod"))
            else:
                self.sandbox = str(kwargs.get("sandbox","prod"))
            self.secret = dict_config.get("secret",kwargs.get("secret"))
            self.org_id = dict_config.get("org_id",kwargs.get("org_id"))
            self.client_id = dict_config.get("client_id",kwargs.get("client_id"))
            self.scopes = dict_config.get("scopes",kwargs.get("scopes"))
        else:
            self.sandbox:str|None = kwargs.get("sandbox","prod")
            self.secret:str|None = kwargs.get("secret")
            self.org_id:str|None = kwargs.get("org_id")
            self.client_id:str|None = kwargs.get("client_id")
            self.scopes:str|None = kwargs.get("scopes")
        if self.sandbox is not None and self.secret is not None and self.org_id is not None and self.client_id is not None and self.scopes is not None:
            print("Configuring connection...")
            self.config = aepp.configure(
                sandbox=self.sandbox,
                secret=self.secret,
                org_id=self.org_id,
                client_id=self.client_id,
                scopes=self.scopes,
                connectInstance=self.connectInstance
            )
            self.prompt = f"{self.config.sandbox}> "
            console.print(Panel(f"Connected to [bold green]{self.sandbox}[/bold green]", style="blue"))

    def _confirm_destructive(self, action:str, target_name:str, warning_lines:list, skip_confirm:bool) -> bool:
        """
        Print a warning panel describing the implications of a destructive action and require the
        user to type the target's name back to confirm. Returns True if the action should proceed.
        """
        body = "\n".join(f"- {line}" for line in warning_lines)
        console.print(Panel(body, title=f"[bold red]WARNING: about to {action} '{target_name}' in sandbox '{self.config.sandbox}'[/bold red]", border_style="red"))
        if skip_confirm:
            return True
        answer = console.input(f"Type the name [bold]{target_name}[/bold] to confirm, or anything else to cancel: ")
        if answer.strip() != target_name:
            console.print("Cancelled. No changes were made.", style="yellow")
            return False
        return True

    def do_create_config_file(self, arg:Any) -> None:
        """Create a configuration file for storing your AEP API connection details."""

        parser = argparse.ArgumentParser(prog='create_config_file', add_help=True)
        parser.add_argument("-fn", "--file_name", help="file name for your config file", default="aepp_config.json",type=str)
        try:
            args = parser.parse_args(shlex.split(arg))
            filename = args.file_name
            aepp.createConfigFile(destination=filename)
            filename_json = filename + ".json" if not filename.endswith(".json") else filename
            console.print(f"Configuration file created at {Path.cwd() / Path(filename_json)}", style="green")
            return
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
            return
        except SystemExit:
            return

    # # --- Commands ---
    def do_config(self, arg:Any) -> None:
        """Pass the different configuration parameters to connect to an AEP instance. Either individually or through a config file with the --config_file option."""
        parser = argparse.ArgumentParser(prog='config', add_help=True)
        parser.add_argument("-sx", "--sandbox", help="Auto-login sandbox")
        parser.add_argument("-s", "--secret", help="Secret")
        parser.add_argument("-o", "--org_id", help="Auto-login org ID")
        parser.add_argument("-sc", "--scopes", help="Scopes")
        parser.add_argument("-cid", "--client_id", help="Auto-login client ID")
        parser.add_argument("-cf", "--config_file", help="Path to config file", default=None)
        try:
            args = parser.parse_args(shlex.split(arg))
            if args.config_file is not None:
                mypath = Path.cwd()
                dict_config = json.load(FileIO(mypath / Path(args.config_file)))
                self.sandbox:str|None = args.sandbox if args.sandbox else dict_config.get("sandbox-name",args.sandbox)
                self.secret:str|None = dict_config.get("secret",args.secret)
                self.org_id:str|None = dict_config.get("org_id",args.org_id)
                self.client_id:str|None = dict_config.get("client_id",args.client_id)
                self.scopes:str|None = dict_config.get("scopes",args.scopes)
                self.connectInstance = True
            else:
                if args.sandbox: self.sandbox = str(args.sandbox)
                if args.secret: self.secret = str(args.secret)
                if args.org_id: self.org_id = str(args.org_id)
                if args.scopes: self.scopes = str(args.scopes)
                if args.client_id: self.client_id = str(args.client_id)
            console.print("Configuring connection...", style="blue")
            self.config = aepp.configure(
                connectInstance=self.connectInstance,
                sandbox=self.sandbox,
                secret=self.secret,
                org_id=self.org_id,
                client_id=self.client_id,
                scopes=self.scopes
            )
            console.print(Panel(f"Connected to [bold green]{self.sandbox}[/bold green]", style="blue"))
            self.prompt = f"{self.config.sandbox}> "
            return
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
            return
        except SystemExit:
            return

    @login_required
    def do_change_sandbox(self, args:Any) -> None:
        """Change the current sandbox after configuration"""
        parser = argparse.ArgumentParser(prog='change sandbox', add_help=True)
        parser.add_argument("sandbox", help="sandbox name to switch to",type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            if args.sandbox is None:
                 console.print(Panel("(!) Please provide a sandbox name using -sx or --sandbox", style="red"))
                 return
            try:
                config_sandbox = sandboxes.Sandboxes(config=self.config)
                list_sandboxes = config_sandbox.getSandboxes()
                sandbox_names = [sb.get("name") for sb in list_sandboxes]
            except Exception as e:
                console.print(Panel(f"(!) Could not verify sandbox names (the Sandboxes API may not be accessible with your current credentials): {str(e)}\nProceeding without validation.", style="yellow"))
                sandbox_names = None
            if sandbox_names is not None and args.sandbox not in sandbox_names:
                console.print(Panel(f"(!) Sandbox '{args.sandbox}' not found in your org. Please provide a valid sandbox name.", style="red"))
                return
            if self.config is not None:
                if args.sandbox:
                    self.config.setSandbox(str(args.sandbox))
                    self.sandbox = str(args.sandbox)
                    self.prompt = f"{self.config.sandbox}> "
                    console.print(Panel(f"Sandbox changed to: [bold green]{self.config.sandbox}[/bold green]", style="blue"))
            else:
                console.print(Panel("(!) You must configure the connection first using the 'config' command.", style="red"))
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_sandboxes(self, args:Any) -> None:
        """List all sandboxes for the current organization"""
        parser = argparse.ArgumentParser(prog='get_sandboxes', add_help=True)
        parser.add_argument("-sv", "--save",help="Save sandboxes to CSV file")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_sandboxes = sandboxes.Sandboxes(config=self.config)
            sandboxes_list = aepp_sandboxes.getSandboxes()
            if sandboxes_list:
                table = Table(title=f"Sandboxes in Org: {self.config.org_id}")
                table.add_column("Name", style="cyan")
                table.add_column("Title", style="magenta")
                table.add_column("Type", style="green")
                table.add_column("Region", style="yellow")
                table.add_column("Created", style="medium_violet_red")
                for sb in sandboxes_list:
                    table.add_row(
                        sb.get("name","N/A"),
                        sb.get("title","N/A"),
                        sb.get("type","N/A"),
                        sb.get("region","N/A"),
                        sb.get("createdDate","N/A"),
                    )
                console.print(table)
                if args.save:
                    df_sandboxes = pd.DataFrame(sandboxes_list)
                    df_sandboxes.to_csv(f"sandboxes_{self.config.org_id}.csv", index=False)
                    console.print(f"Sandboxes exported to sandboxes_{self.config.org_id}.csv", style="green")
            else:
                console.print("(!) No sandboxes found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
        
    @login_required
    def do_create_sandbox(self,args:Any)->None:
        """
        Create a new sandbox in the current organization. 
        """
        parser = argparse.ArgumentParser(prog='create_sandbox', add_help=True)
        parser.add_argument("-n","--name", help="Name for the new sandbox. It must be unique and not contain spaces (use - instead of space)", required=True, type=str)
        parser.add_argument('-tl','--title', help="Title for the new sandbox", required=True, type=str)
        parser.add_argument("-t","--type", help="Type for the new sandbox. Possible values: [development, production]", required=True, type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            if args.type not in ['development', 'production']:
                console.print(f"(!) Error: Invalid sandbox type '{args.type}'. Must be either 'development' or 'production'.", style="red")
                return
            if args.name and ' ' in args.name:
                console.print(f"(!) Error: Sandbox name '{args.name}' cannot contain spaces. Please use '-' instead of space.", style="red")
                return
            aepp_sandboxes = sandboxes.Sandboxes(config=self.config)
            res = aepp_sandboxes.createSandbox(name=args.name, title=args.title, type_sandbox=args.type)
            if res.get("name"):
                console.print_json(data=res, style="green")
            else:
                console.print_json(data=res, style="orange_red1")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_profile_attributes_lineage(self,args:Any)->None:
        """Get data lineage information for all profile paths. This method is very expensive and will take a long time. Use with caution."""
        parser = argparse.ArgumentParser(prog='get_profile_paths_info', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            if self.ups_profile_analyzer is None:
                console.print("Initializing Profile UPS Fields Analyzer. This will take few minutes...", style="blue")
                self.ups_profile_analyzer = UpsFieldsAnalyzer(config=self.config)
            else:
                if self.config.sandbox != self.ups_profile_analyzer.sandbox:
                    console.print("Re-initializing Profile UPS Fields Analyzer for the new sandbox. This will take few minutes...", style="blue")
                    self.ups_profile_analyzer = UpsFieldsAnalyzer(config=self.config)
            console.print("Analyzing all Profile paths information. This will take few minutes...", style="blue")
            df_analysis:pd.DataFrame = self.ups_profile_analyzer.analyzePaths(output='df')
            if df_analysis is not None:
                console.print(df_analysis)
                df_analysis.to_csv(f"profile_all_paths_info.csv", index=False)
                console.print(f"Profile all paths information data exported to profile_all_paths_info.csv", style="green")
            else:
                console.print("(!) No profile paths information data found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
        
    @login_required
    def do_get_profile_attribute_lineage(self, args:Any) -> None:
        """Get data lineage information for a specific profile path. This method is expensive and will take a long time. Use with caution."""
        parser = argparse.ArgumentParser(prog='get_profile_path_info', add_help=True)
        parser.add_argument("path", help="Dot notation of the path to analyze in Profile Storage", default=None,type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            if self.ups_profile_analyzer is None:
                console.print("Initializing Profile UPS Fields Analyzer. This will take few minutes...", style="blue")
                self.ups_profile_analyzer = UpsFieldsAnalyzer(config=self.config)
            else:
                if self.config.sandbox != self.ups_profile_analyzer.sandbox:
                    console.print("Re-initializing Profile UPS Fields Analyzer for the new sandbox. This will take few minutes...", style="blue")
                    self.ups_profile_analyzer = UpsFieldsAnalyzer(config=self.config)
            analysis = self.ups_profile_analyzer.analyzePath(args.path)
            if analysis:
                console.print_json(data=analysis)
                with open(f"profile_path_info_{args.path.replace('/','_')}.json", 'w') as f:
                    json.dump(analysis, f, indent=4)
                console.print(f"Profile path information data exported to profile_path_info_{args.path.replace('/','_')}.json", style="green")
            else:
                console.print("(!) No profile path information data found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_event_attributes_lineage(self,args:Any)->None:
        """Get data lineage information for all Experience Event paths. This method is very expensive and will take a long time. Use with caution."""
        parser = argparse.ArgumentParser(prog='get_event_paths_info', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            if self.ups_profile_analyzer is None:
                console.print("Initializing Event UPS Fields Analyzer. This will take few minutes...", style="blue")
                self.ups_profile_analyzer = UpsFieldsAnalyzer(config=self.config,union='https://ns.adobe.com/xdm/context/experienceevent__union')
            else:
                if self.config.sandbox != self.ups_profile_analyzer.sandbox:
                    console.print("Re-initializing Event UPS Fields Analyzer for the new sandbox. This will take few minutes...", style="blue")
                    self.ups_profile_analyzer = UpsFieldsAnalyzer(config=self.config,union='https://ns.adobe.com/xdm/context/experienceevent__union')
            console.print("Analyzing all Event paths information. This will take few minutes...", style="blue")
            df_analysis:pd.DataFrame = self.ups_profile_analyzer.analyzePaths(output='df')
            if df_analysis is not None:
                console.print(df_analysis)
                df_analysis.to_csv(f"event_all_paths_info.csv", index=False)
                console.print(f"Event all paths information data exported to event_all_paths_info.csv", style="green")
            else:
                console.print("(!) No event paths information data found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_event_attribute_lineage(self, args:Any) -> None:
        """Get data lineage information for a specific Experience Event path. This method is expensive and will take a long time. Use with caution."""
        parser = argparse.ArgumentParser(prog='get_event_path_info', add_help=True)
        parser.add_argument("path", help="Dot notation of the path to analyze in Experience Event Storage", default=None,type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            if self.ups_profile_analyzer is None:
                console.print("Initializing Event UPS Fields Analyzer. This will take few minutes...", style="blue")
                self.ups_profile_analyzer = UpsFieldsAnalyzer(config=self.config,union='https://ns.adobe.com/xdm/context/experienceevent__union')
            else:
                if self.config.sandbox != self.ups_profile_analyzer.sandbox:
                    console.print("Re-initializing Event UPS Fields Analyzer for the new sandbox. This will take few minutes...", style="blue")
                    self.ups_profile_analyzer = UpsFieldsAnalyzer(config=self.config,union='https://ns.adobe.com/xdm/context/experienceevent__union')
            analysis = self.ups_profile_analyzer.analyzePath(args.path)
            if analysis:
                console.print_json(data=analysis)
                with open(f"event_path_info_{args.path.replace('/','_')}.json", 'w') as f:
                    json.dump(analysis, f, indent=4)
                console.print(f"Event path information data exported to event_path_info_{args.path.replace('/','_')}.json", style="green")
            else:
                console.print("(!) No event path information data found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_schemas(self, args:Any) -> None:
        """List all schemas in the current sandbox. By default do not save the output to a file as it can be very long, use the --save option to export the data to a CSV file."""
        parser = argparse.ArgumentParser(prog='get_schemas', add_help=True)
        parser.add_argument("-sv", "--save",help="Save schemas to CSV file")
        parser.add_argument("-f","--filter",help="filter the schema return by name (non-case sensitive and partial match)",type=str,default="")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            schemas = aepp_schema.getSchemas()
            if args.filter != "":
                schemas = [sc for sc in schemas if args.filter.lower() in sc['title'].lower()]
            if len(schemas) > 0:
                table = Table(title=f"Schemas in Sandbox: {self.config.sandbox}")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="magenta")
                table.add_column("Version", style="green")
                for sch in schemas:
                    table.add_row(
                        sch.get("meta:altId","N/A"),
                        sch.get("title","N/A"),
                        str(sch.get("version","N/A")),
                    )
                console.print(table)
                if args.save:
                    df_schemas = pd.DataFrame(schemas)
                    df_schemas.to_csv(f"{self.config.sandbox}_schemas.csv", index=False)
                    console.print(f"Schemas exported to {self.config.sandbox}_schemas.csv", style="green")
            else:
                console.print("(!) No schemas found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_classes(self,args) -> None:
        """List all classes in the current sandbox. By default do not save the output to a file as it can be very long, use the --save option to export the data to a CSV file."""
        parser = argparse.ArgumentParser(prog='get_classes', add_help=True)
        parser.add_argument("-sv", "--save",help="Save classes to CSV file",type=str2bool,default=False)
        parser.add_argument("-f","--filter",help="filter the class return by name (non-case sensitive and partial match)",type=str,default="")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            classes = aepp_schema.getClasses()
            global_classes = aepp_schema.getClassesGlobal()
            all_classes = [{'$id':cls.get('$id'), 'title':cls.get('title'), 'version':cls.get('version')} for cls in classes + global_classes]
            if args.filter != "":
                all_classes = [cls for cls in all_classes if args.filter.lower() in cls['title'].lower()]
            if len(all_classes) > 0:
                table = Table(title=f"Classes in Sandbox: {self.config.sandbox}")
                table.add_column("$ID", style="cyan")
                table.add_column("Name", style="magenta")
                for cl in all_classes:
                    table.add_row(
                        cl.get("$id","N/A"),
                        cl.get("title","N/A"),
                    )
                console.print(table)
                if args.save:
                    df_classes = pd.DataFrame(all_classes)
                    df_classes.to_csv(f"{self.config.sandbox}_classes.csv", index=False)
                    console.print(f"Classes exported to {self.config.sandbox}_classes.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
            


    @login_required
    def do_get_ups_schemas(self, args) -> None:
        """List all schemas enabled for Profile in the current sandbox. By default do not save the output to a file as it can be very long, use the --save option to export the data to a CSV file."""
        parser = argparse.ArgumentParser(prog='get_ups_schemas', add_help=True)
        parser.add_argument("-sv", "--save",help="Boolean. Save enabled schemas to CSV file. Default False. Possible values: True, False",type=str2bool,default=False)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            union_schemas = aepp_schema.getUnions()
            schemas = aepp_schema.getSchemas()
            enabled_schemas = []
            for union in union_schemas:
                for member in union.get("meta:extends",[]):
                    if 'schema' in member:
                        enabled_schemas.append(member)
            list_enabled_schemas = []
            list_enabled_schemas = [sc for sc in schemas if sc.get("$id") in enabled_schemas]
            if len(list_enabled_schemas) > 0:
                table = Table(title=f"Enabled Schemas in Sandbox: {self.config.sandbox}")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="magenta")
                table.add_column("Version", style="green")
                for sch in list_enabled_schemas:
                    table.add_row(
                        sch.get("meta:altId","N/A"),
                        sch.get("title","N/A"),
                        str(sch.get("version","N/A")),
                    )
                console.print(table)
                if args.save:
                    df_schemas = pd.DataFrame(list_enabled_schemas)
                    df_schemas.to_csv(f"{self.config.sandbox}_enabled_schemas.csv", index=False)
                    console.print(f"Enabled Schemas exported to {self.config.sandbox}_enabled_schemas.csv", style="green")
            else:
                console.print("(!) No enabled schemas found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_ups_fieldgroups(self, args:Any) -> None:
        """List all field groups enabled for Profile in the current sandbox. By default do not save the output to a file as it can be very long, use the --save option to export the data to a CSV file."""
        parser = argparse.ArgumentParser(prog='get_fieldgroups_enabled', add_help=True)
        parser.add_argument("-sv", "--save",help="Boolean. Save enabled field groups to CSV file. Default False. Possible values: True, False",type=str2bool,default=False)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            union_schemas = aepp_schema.getUnions()
            fgs = aepp_schema.getFieldGroups()
            enabled_fgs = []
            for union in union_schemas:
                for member in union.get("meta:extends",[]):
                    if 'mixins' in member:
                        enabled_fgs.append(member)
            list_enabled_fgs = []
            list_enabled_fgs = [f for f in fgs if f.get("$id") in enabled_fgs]
            if len(list_enabled_fgs) > 0:
                table = Table(title=f"Enabled Field Groups in Sandbox: {self.config.sandbox}")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="magenta")
                table.add_column("Version", style="green")
                for sch in list_enabled_fgs:
                    table.add_row(
                        sch.get("meta:altId","N/A"),
                        sch.get("title","N/A"),
                        str(sch.get("version","N/A")),
                    )
                console.print(table)
                if args.save:
                    df_fgs = pd.DataFrame(list_enabled_fgs)
                    df_fgs.to_csv(f"{self.config.sandbox}_enabled_field_groups.csv", index=False)
                    console.print(f"Enabled Field Groups exported to {self.config.sandbox}_enabled_field_groups.csv", style="green")
            else:
                console.print("(!) No enabled field groups found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
        
    @login_required
    def do_create_b2b_artifacts(self,args:Any) -> None:
        """
        Create the B2B identities and schema relationship for the current sandbox
        """
        parser = argparse.ArgumentParser(prog="create_b2b_artifacts",add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_identity = identity.Identity(config=self.config)
            aepp_schema = schema.Schema(config=self.config)
            new_identities = aepp_identity.createB2BIdentities()
            new_schemas = aepp_schema.createB2Bschemas()
            result = {
                "identities":new_identities,
                "schemas": list(new_schemas.keys())
            }
            console.print_json(data=result)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return



    @login_required
    def do_get_profile_schemas(self,args:Any) -> None:
        """Get the current schema based on Profile class. By default do not save the output to a file as it can be very long, use the --save option to export the data to a CSV file."""
        parser = argparse.ArgumentParser(prog='get_profile_schemas', add_help=True)
        parser.add_argument("-sv", "--save",help="Boolean. Save profile schemas to CSV file. Default False. Possible values: True, False",type=str2bool,default=False)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            profile_schemas = aepp_schema.getSchemas(classFilter="https://ns.adobe.com/xdm/context/profile")
            if profile_schemas:
                table = Table(title=f"Profile Schemas in Sandbox: {self.config.sandbox}")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="magenta")
                table.add_column("Version", style="green")
                for sch in profile_schemas:
                    table.add_row(
                        sch.get("meta:altId","N/A"),
                        sch.get("title","N/A"),
                        str(sch.get("version","N/A")),
                    )
                console.print(table)
                if args.save:
                    df_schemas = pd.DataFrame(profile_schemas)
                    df_schemas.to_csv(f"{self.config.sandbox}_profile_schemas.csv", index=False)
                    console.print(f"Profile Schemas exported to {self.config.sandbox}_profile_schemas.csv", style="green")
            else:
                console.print("(!) No profile schemas found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_union_profile_json(self,args:Any) -> None:
        """Get the current Profile union schema JSON structure and saving it in a file. It is the Profile schema that contains all enabled Profile class based schemas"""
        parser = argparse.ArgumentParser(prog='get_union_profile', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            profile_union = schemamanager.SchemaManager('https://ns.adobe.com/xdm/context/profile__union',config=self.config)
            data = profile_union.to_dict()
            with open(f"{self.config.sandbox}_profile_union_schema.json", 'w') as f:
                json.dump(data, f, indent=4)
            console.print(f"Profile Union Schema exported to {self.config.sandbox}_profile_union_schema.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_union_profile_csv(self,args:Any) -> None:
        """Get the current Profile union schema CSV structure and saving it in a file. It is the Profile schema that contains all enabled Profile class based schemas"""
        parser = argparse.ArgumentParser(prog='get_union_profile', add_help=True)
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full schema information with all details. Default False. Possible values: True, False",type=str2bool)
        try:
            args = parser.parse_args(shlex.split(args))
            profile_union = schemamanager.SchemaManager('https://ns.adobe.com/xdm/context/profile__union',config=self.config)
            df = profile_union.to_dataframe(full=args.full)
            df.to_csv(f"{self.config.sandbox}_profile_union_schema.csv", index=False)
            console.print(f"Profile Union Schema exported to {self.config.sandbox}_profile_union_schema.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_union_event_json(self,args:Any) -> None:
        """Get the current Experience Event union schema JSON structure and saving it in a file. It is the Experience Event schema that contains all enabled Experience Event class based schemas"""
        parser = argparse.ArgumentParser(prog='get_union_event', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            event_union = schemamanager.SchemaManager('https://ns.adobe.com/xdm/context/experienceevent__union',config=self.config)
            data = event_union.to_dict()
            with open(f"{self.config.sandbox}_event_union_schema.json", 'w') as f:
                json.dump(data, f, indent=4)
            console.print(f"Event Union Schema exported to {self.config.sandbox}_event_union_schema.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_union_event_csv(self,args:Any) -> None:
        """Get the current Experience Event union schema CSV structure and saving it in a file. It is the Experience Event schema that contains all enabled Experience Event class based schemas"""
        parser = argparse.ArgumentParser(prog='get_union_event', add_help=True)
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full schema information with all details. Default False. Possible values: True, False",type=str2bool)
        try:
            args = parser.parse_args(shlex.split(args))
            event_union = schemamanager.SchemaManager('https://ns.adobe.com/xdm/context/experienceevent__union',config=self.config)
            df = event_union.to_dataframe(full=args.full)
            df.to_csv(f"{self.config.sandbox}_event_union_schema.csv", index=False)
            console.print(f"Event Union Schema exported to {self.config.sandbox}_event_union_schema.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_event_schemas(self,args:Any) -> None:
        """Get all the schemas using the Experience Event class as filter. By default do not save the output to a file as it can be very long, use the --save option to export the data to a CSV file."""
        parser = argparse.ArgumentParser(prog='get_event_schemas', add_help=True)
        parser.add_argument("-sv", "--save",help="Boolean. Save event schemas to CSV file. Default False. Possible values: True, False",type=str2bool,default=False)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            event_schemas = aepp_schema.getSchemas(classFilter="https://ns.adobe.com/xdm/context/experienceevent")
            if args.save:
                df_schemas = pd.DataFrame(event_schemas)
                df_schemas.to_csv(f"{self.config.sandbox}_event_schemas.csv", index=False)
                console.print(f"Event Schemas exported to {self.config.sandbox}_event_schemas.csv", style="green")
            if event_schemas:
                table = Table(title=f"Event Schemas in Sandbox: {self.config.sandbox}")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="magenta")
                table.add_column("Version", style="green")
                for sch in event_schemas:
                    table.add_row(
                        sch.get("meta:altId","N/A"),
                        sch.get("title","N/A"),
                        str(sch.get("version","N/A")),
                    )
                console.print(table)
            else:
                console.print("(!) No event schemas found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return         

    @login_required
    def do_get_schema_xdm(self, arg:Any) -> None:
        """Get schema XDM JSON by name or $ID or alt:Id. By default it will save the output in a JSON file with the name of the schema title, use the --full option to get the full schema with all details but beware that it can be very long."""
        parser = argparse.ArgumentParser(prog='get_schema_xdm', add_help=True)
        parser.add_argument("schema", help="Schema title, $id or alt:Id to retrieve")
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full schema with all details. Default False. Possible values: True, False",type=str2bool)
        try:
            args = parser.parse_args(shlex.split(arg))
            aepp_schema = schema.Schema(config=self.config)
            schemas = aepp_schema.getSchemas()
            print(args.schema)
            ## chech if schema title is found
            if args.schema in [sch for sch in aepp_schema.data.schemas_altId.keys()]:
                schema_json = aepp_schema.getSchema(
                    schemaId=aepp_schema.data.schemas_altId[args.schema],
            )
            else:
                
                schema_json = aepp_schema.getSchema(
                    schemaId=args.schema
            )
            if 'title' in schema_json.keys():
                filename = f"{schema_json['title']}_xdm.json"
                with open(filename, 'w') as f:
                    json.dump(schema_json, f, indent=4)
                console.print(f"Schema '{args.schema}' saved to {filename}.", style="green")
            else:
                console.print(f"(!) Schema '{args.schema}' not found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_schema_csv(self, arg:Any) -> None:
        """Get schema CSV by name or ID. Use the --full option to get the full schema information with all details."""
        parser = argparse.ArgumentParser(prog='get_schema_csv', add_help=True)
        parser.add_argument("schema", help="Schema $id or alt:Id to retrieve")
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full schema information with all details. Default False. Possible values: True, False",type=str2bool)
        try:
            args = parser.parse_args(shlex.split(arg))
            aepp_schema = schema.Schema(config=self.config)
            schemas = aepp_schema.getSchemas()
            ## chech if schema title is found
            if args.schema in [sch for sch in aepp_schema.data.schemas_altId.keys()]:
                my_schema_manager = schemamanager.SchemaManager(
                    schema=aepp_schema.data.schemas_altId[args.schema],
                    config=self.config
                )
                df = my_schema_manager.to_dataframe(full=args.full)
            else:
                my_schema_manager = schemamanager.SchemaManager(
                    schema=args.schema,
                    config=self.config
                )
            df = my_schema_manager.to_dataframe(full=args.full)
            df.to_csv(f"{my_schema_manager.title}_schema.csv", index=False)
            console.print(f"Schema exported to {my_schema_manager.title}_schema.csv", style="green")  
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_schema_json(self, args:Any) -> None:
        """Get schema JSON representation by name or ID."""
        parser = argparse.ArgumentParser(prog='get_schema_json', add_help=True)
        parser.add_argument("schema", help="Schema $id or alt:Id to retrieve")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            schemas = aepp_schema.getSchemas()
            ## chech if schema title is found
            if args.schema in [sch for sch in aepp_schema.data.schemas_altId.keys()]:
                my_schema_manager = schemamanager.SchemaManager(
                    schema=aepp_schema.data.schemas_altId[args.schema],
                    config=self.config
                )
            else:
                my_schema_manager = schemamanager.SchemaManager(
                    schema=args.schema,
                    config=self.config
                )
            data = my_schema_manager.to_dict()
            with open(f"{my_schema_manager.title}.json", 'w') as f:
                json.dump(data, f, indent=4)
            console.print(f"Schema exported to {my_schema_manager.title}.json", style="green")  
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_fieldgroups(self, args:Any) -> None:
        """List all field groups in the current sandbox"""
        parser = argparse.ArgumentParser(prog='get_fieldgroups', add_help=True)
        parser.add_argument('-ootb','--ootb',help="Boolean. Include out-of-the-box field groups. Default False. Possible values: True, False",type=str2bool,default=False)
        parser.add_argument('-f','--filter',help="filtering the field groups based on the string",type=str,default=None)
        parser.add_argument("-sv", "--save",help="Boolean. Save field groups to CSV file. Default False. Possible values: True, False",type=str2bool,default=False)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            if not args.ootb:
                fieldgroups = aepp_schema.getFieldGroups()
            else:
                fieldgroups = aepp_schema.getFieldGroupsGlobal()
            if args.filter:
                fieldgroups = [fg for fg in fieldgroups if args.filter.lower() in fg.get("title","").lower()]
            if args.save and fieldgroups:
                df_fgs = pd.DataFrame(fieldgroups)
                if args.ootb:
                    df_fgs.to_csv(f"{self.config.sandbox}_fieldgroups_ootb.csv",index=False)
                else:
                    df_fgs.to_csv(f"{self.config.sandbox}_fieldgroups.csv",index=False)
            if fieldgroups:
                table = Table(title=f"Field Groups in Sandbox: {self.config.sandbox}")
                table.add_column("altId", style="cyan")
                table.add_column("Title", style="magenta")
                for fg in fieldgroups:
                    table.add_row(
                        fg.get("meta:altId","N/A"),
                        fg.get("title","N/A"),
                    )
                console.print(table)
                if args.save:
                    if args.ootb:
                        console.print(f"Field Groups exported to {self.config.sandbox}_fieldgroups_ootb.csv", style="green")
                    else:
                        console.print(f"Field Groups exported to {self.config.sandbox}_fieldgroups.csv", style="green")
            else:
                console.print("(!) No field groups found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_fieldgroup_json(self, args:Any) -> None:
        """Get field group JSON by name or ID"""
        parser = argparse.ArgumentParser(prog='get_fieldgroup_json', add_help=True)
        parser.add_argument("fieldgroup", help="Field Group name, $id or alt:Id to retrieve")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            fieldgroups = aepp_schema.getFieldGroups()
            fieldgroupsglobal = aepp_schema.getFieldGroupsGlobal()
            ## chech if schema title is found
            if args.fieldgroup in [fg for fg in aepp_schema.data.fieldGroups_altId.keys()]:
                my_fieldgroup_manager = fieldgroupmanager.FieldGroupManager(
                    fieldGroup=aepp_schema.data.fieldGroups_altId[args.fieldgroup],
                    config=self.config
                )
            else:
                my_fieldgroup_manager = fieldgroupmanager.FieldGroupManager(
                    fieldGroup=args.fieldgroup,
                    config=self.config
                )
            data = my_fieldgroup_manager.to_dict()
            with open(f"{my_fieldgroup_manager.title}_fieldgroup.json", 'w') as f:
                json.dump(data, f, indent=4)
            console.print(f"Field Group exported to {my_fieldgroup_manager.title}_fieldgroup.json", style="green")  
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_fieldgroup_csv(self, args:Any) -> None:
        """Get field group CSV by name or ID"""
        parser = argparse.ArgumentParser(prog='get_fieldgroup_csv', add_help=True)
        parser.add_argument("fieldgroup", help="Field Group name, $id or alt:Id to retrieve")
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full field group information with all details. Default False. Possible values: True, False",type=str2bool)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            fieldgroups = aepp_schema.getFieldGroups()
            fieldgroupsglobal = aepp_schema.getFieldGroupsGlobal()
            ## chech if schema title is found
            if args.fieldgroup in [fg for fg in aepp_schema.data.fieldGroups_altId.keys()]:
                my_fieldgroup_manager = fieldgroupmanager.FieldGroupManager(
                    fieldGroup=aepp_schema.data.fieldGroups_altId[args.fieldgroup],
                    config=self.config
                )
            else:
                my_fieldgroup_manager = fieldgroupmanager.FieldGroupManager(
                    fieldGroup=args.fieldgroup,
                    config=self.config
                )
            df = my_fieldgroup_manager.to_dataframe(full=args.full)
            df.to_csv(f"{my_fieldgroup_manager.title}_fieldgroup.csv", index=False)
            console.print(f"Field Group exported to {my_fieldgroup_manager.title}_fieldgroup.csv", style="green")  
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_fieldgroup_xdm(self,args:Any)->None:
        """Get the field group XDM definition by name or ID """
        parser = argparse.ArgumentParser(prog='get_fieldgroup_xdm', add_help=True)
        parser.add_argument("fieldgroup", help="Field Group name, $id or alt:Id to retrieve")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            fieldgroups = aepp_schema.getFieldGroups()
            ## chech if schema title is found
            if args.fieldgroup in [fg for fg in aepp_schema.data.fieldGroups_altId.keys()]:
                my_fieldgroup_manager = fieldgroupmanager.FieldGroupManager(
                    fieldGroup=aepp_schema.data.fieldGroups_altId[args.fieldgroup],
                    config=self.config
                )
            else:
                my_fieldgroup_manager = fieldgroupmanager.FieldGroupManager(
                    fieldGroup=args.fieldgroup,
                    config=self.config
                )
            fieldgroup_json = my_fieldgroup_manager.to_xdm()
            filename = f"{my_fieldgroup_manager.title}_xdm.json"
            with open(filename, 'w') as f:
                json.dump(fieldgroup_json, f, indent=4)
            console.print(f"Field Group XDM definition saved to {filename}.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_datatypes(self, args:Any) -> None:
        """List all data types in the current sandbox"""
        parser = argparse.ArgumentParser(prog='get_datatypes', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            datatypes = aepp_schema.getDataTypes()
            if datatypes:
                table = Table(title=f"Data Types in Sandbox: {self.config.sandbox}")
                table.add_column("altId", style="cyan")
                table.add_column("Title", style="magenta")
                for dt in datatypes:
                    table.add_row(
                        dt.get("meta:altId","N/A"),
                        dt.get("title","N/A"),
                    )
                console.print(table)
            else:
                console.print("(!) No data types found.", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_datatype_csv(self, args:Any) -> None:
        """Get data type CSV by name or ID"""
        parser = argparse.ArgumentParser(prog='get_datatype_csv', add_help=True)
        parser.add_argument("datatype", help="Data Type name, $id or alt:Id to retrieve")
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full data type information with all details. Default False. Possible values: True, False",type=str2bool)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            datatypes = aepp_schema.getDataTypes()
            ## chech if schema title is found
            if args.datatype in [dt for dt in aepp_schema.data.dataTypes_altId.keys()]:
                my_datatype_manager = datatypemanager.DataTypeManager(
                    dataType=aepp_schema.data.dataTypes_altId[args.datatype],
                    config=self.config
                )
            else:
                my_datatype_manager = datatypemanager.DataTypeManager(
                    dataType=args.datatype,
                    config=self.config
                )
            df = my_datatype_manager.to_dataframe(full=args.full)
            df.to_csv(f"{my_datatype_manager.title}_datatype.csv", index=False)
            console.print(f"Data Type exported to {my_datatype_manager.title}_datatype.csv", style="green")  
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_datatype_json(self, args:Any) -> None:
        """Get data type JSON by name or ID"""
        parser = argparse.ArgumentParser(prog='get_datatype_json', add_help=True)
        parser.add_argument("datatype", help="Data Type name, $id or alt:Id to retrieve")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            datatypes = aepp_schema.getDataTypes()
            ## chech if schema title is found
            if args.datatype in [dt for dt in aepp_schema.data.dataTypes_altId.keys()]:
                my_datatype_manager = datatypemanager.DataTypeManager(
                    dataType=aepp_schema.data.dataTypes_altId[args.datatype],
                    config=self.config
                )
            else:
                my_datatype_manager = datatypemanager.DataTypeManager(
                    dataType=args.datatype,
                    config=self.config
                )
            data = my_datatype_manager.to_dict()
            with open(f"{my_datatype_manager.title}_datatype.json", 'w') as f:
                json.dump(data, f, indent=4)
            console.print(f"Data Type exported to {my_datatype_manager.title}_datatype.json", style="green")  
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
        
    @login_required
    def do_get_datatype_xdm(self, args:Any) -> None:
        """Get data type XDM JSON by name or ID"""
        parser = argparse.ArgumentParser(prog='get_datatype_xdm', add_help=True)
        parser.add_argument("datatype", help="Data Type name, $id or alt:Id to retrieve")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            datatypes = aepp_schema.getDataTypes()
            ## chech if schema title is found
            if args.datatype in [dt for dt in aepp_schema.data.dataTypes_altId.keys()]:
                my_datatype_manager = datatypemanager.DataTypeManager(
                    dataType=aepp_schema.data.dataTypes_altId[args.datatype],
                    config=self.config
                )
            else:
                my_datatype_manager = datatypemanager.DataTypeManager(
                    dataType=args.datatype,
                    config=self.config
                )
            datatype_json = my_datatype_manager.to_xdm()
            filename = f"{my_datatype_manager.title}_xdm.json"
            with open(filename, 'w') as f:
                json.dump(datatype_json, f, indent=4)
            console.print(f"Data Type XDM definition saved to {filename}.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_descriptors(self, args:Any) -> None:
        """Retrieve the list of descriptors, possibly for a specific schema"""
        parser = argparse.ArgumentParser(prog='get_descriptors', add_help=True)
        parser.add_argument("-sc", "--schema", help="Schema name, $id or alt:Id to filter descriptors by schema")
        parser.add_argument("-sv", "--save",help="Boolean. Save descriptors to JSON file. Default False. Possible values: True, False",type=str2bool,default=False)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            schemas = aepp_schema.getSchemas()
            if args.schema:
                ## chech if schema title is found
                if args.schema in [sch for sch in aepp_schema.data.schemas_altId.keys()]:
                    schema_id = aepp_schema.data.schemas_id[args.schema]
                else:
                    if args.schema in aepp_schema.data.schemas_altId.values():
                        schema_id = f"https://ns.adobe.com/henkel/schemas/{args.schema.split(".").pop()}"
                    else:
                        schema_id = args.schema
                descriptors = aepp_schema.getDescriptors(prop=f"xdm:sourceSchema=={schema_id}")
            else:
                descriptors = aepp_schema.getDescriptors()
            if descriptors:
                table = Table(title=f"Descriptors in Sandbox: {self.config.sandbox}")
                table.add_column("id", style="cyan")
                table.add_column("Type", style="magenta")
                table.add_column("Source Path", style="green")
                table.add_column("Source Schema", style="yellow")
                for desc in descriptors:
                    if type(desc.get("xdm:sourceProperty","N/A")) == list:
                        srcProperty =  ','.join(desc.get("xdm:sourceProperty"))
                    else:
                        srcProperty = desc.get("xdm:sourceProperty","N/A")
                    table.add_row(
                        desc.get("@id","N/A"),
                        desc.get("@type","N/A"),
                        srcProperty,
                        desc.get("xdm:sourceSchema","N/A")
                    )
                console.print(table)
            else:
                console.print(f"No descriptor found", style="red")
            if args.save:
                if args.schema:
                    filename = f"descriptors_{args.schema}.json"
                else:
                    filename = f"descriptors.json"
                with open(filename, 'w') as f:
                    json.dump(descriptors, f, indent=4)
                console.print(f"Descriptors saved to {filename}.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_descriptor(self, args:Any)->None:
        """Get a descriptor by ID; use -sv/--save to export descriptor_<id>.json."""
        parser = argparse.ArgumentParser(prog='get_descriptor', add_help=True)
        parser.add_argument("descriptor_id", help="Descriptor ID to retrieve")
        parser.add_argument("-sv","--save", help="Save the descriptor to a file", default=False, action="store_true")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            descriptor = aepp_schema.getDescriptor(descriptorId=args.descriptor_id)
            if descriptor:
                if not descriptor.get("@id"):
                    raise ValueError(f"Descriptor retrieval failed: {descriptor}")
                console.print_json(data=descriptor)
                if args.save:
                    filename = f"descriptor_{args.descriptor_id}.json"
                    with open(filename, 'w') as f:
                        json.dump(descriptor, f, indent=4)
                    console.print(f"Descriptor saved to {filename}.", style="green")
            else:
                console.print(f"No descriptor found with ID '{args.descriptor_id}'", style="red")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_enable_schema_for_ups(self, args:Any) -> None:
        """Enable a schema for Profile"""
        parser = argparse.ArgumentParser(prog='enable_schema_for_ups', add_help=True)
        parser.add_argument("schema_id", help="Schema ID to enable for Profile")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            result = aepp_schema.enableSchemaForUPS(schemaId=args.schema_id)
            console.print(f"Schema '{args.schema_id}' enabled for Profile.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_create_fieldgroup_template(self, args:Any) -> None:
        """Create a field group definition template CSV file"""
        parser = argparse.ArgumentParser(prog='create_fieldgroup_definition_template', add_help=True)
        parser.add_argument("-tl", "--title", help="Name of the field group",default="MyFieldGroup",type=str)
        parser.add_argument("-d","--description", help="Description of the field group", default="",type=str)
        parser.add_argument("-fn","--file_name", help="Name of the output CSV file", default=None,type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            myfg = fieldgroupmanager.FieldGroupManager(config=self.config,title=args.title,description=args.description,file_name=args.file_name)
            df_template = myfg.createFieldGroupTemplate()
            if args.file_name:
                if 'csv' not in args.file_name:
                    filename = f"{args.file_name}.csv"
                else:
                    filename = args.file_name
            else:
                filename = f"{myfg.title}.csv"
            df_template.to_csv(filename, index=False)
            console.print(f"Field Group definition template CSV created: {filename}", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_upload_fieldgroup_definition_csv(self,args:Any) -> None:
        """Upload a field group definition from a CSV file"""
        parser = argparse.ArgumentParser(prog='upload_fieldgroup_definition_csv', add_help=True)
        parser.add_argument("csv_path", help="Path to the field group CSV file")
        parser.add_argument("-sp","--separator", help="CSV separator, default is comma (,)", default=",", type=str)
        parser.add_argument("-ts","--test",help="Boolean. Test creation without uploading it to AEP. It will output a JSON file. Default False. Possible values: True, False",default=False,type=str2bool)
        try:
            args = parser.parse_args(shlex.split(args))
            myfg = fieldgroupmanager.FieldGroupManager(config=self.config)
            myfg.importFieldGroupDefinition(fieldgroup=args.csv_path, sep=args.separator)
            if args.test:
                data = myfg.to_dict()
                with open(f"test_{myfg.title}_fieldgroup.json", 'w') as f:
                    json.dump(data, f, indent=4)
                console.print(f"Field Group definition test exported to test_{myfg.title}_fieldgroup.json", style="green")
                console.print_json(data=data)
                return
            res = myfg.createFieldGroup()
            console.print(f"Field Group uploaded with ID: {res.get('meta:altId')}", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_upload_fieldgroup_definition_xlsx(self, args:Any) -> None:
        """Upload a field group definition from an Excel file"""
        parser = argparse.ArgumentParser(prog='upload_fieldgroup_definition_xlsx', add_help=True)
        parser.add_argument("xlsx_path", help="Path to the field group Excel file")
        parser.add_argument("-sh","--sheet", help="Sheet name in the Excel file", default="Sheet1", type=str)
        parser.add_argument("-ts","--test",help="Boolean. Test creation without uploading it to AEP. It will output a JSON file. Default False. Possible values: True, False",default=False,type=str2bool)
        try:
            args = parser.parse_args(shlex.split(args))
            myfg = fieldgroupmanager.FieldGroupManager(config=self.config)
            myfg.importFieldGroupDefinition(fieldgroup=args.xlsx_path, sheet_name=args.sheet)
            if args.test:
                data = myfg.to_dict()
                with open(f"test_{myfg.title}_fieldgroup.json", 'w') as f:
                    json.dump(data, f, indent=4)
                console.print(f"Field Group definition test exported to test_{myfg.title}_fieldgroup.json", style="green")
                console.print_json(data=data)
                return
            res = myfg.createFieldGroup()
            console.print(f"Field Group uploaded with ID: {res.get('meta:altId')}", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_delete_fieldgroup(self,args:Any) -> None:
        parser = argparse.ArgumentParser(prog="delete_fieldgroup",add_help=True)
        parser.add_argument("fieldgroup",help="Field Group Name or ID to be deleted")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            fieldgroups = aepp_schema.getFieldGroups()
            ## chech if schema title is found
            if args.fieldgroup in [fg for fg in aepp_schema.data.fieldGroups_altId.keys()]:
                fg_id = aepp_schema.data.fieldGroups_altId[args.fieldgroup]
            elif args.fieldgroup in aepp_schema.data.fieldGroups_altId.values() or args.fieldgroup in aepp_schema.data.fieldGroups_id.values():
                fg_id = args.fieldgroup
            else:
                console.print("required a field group name or ID to delete", style="red")
                return
            res = aepp_schema.deleteFieldGroup(fg_id)
            if res != 204 and res != "204":
                console.print(f"(!) Error: Field Group '{args.fieldgroup}' could not be deleted. Response code: {res}", style="red")
            else:
                console.print(f"Field Group '{args.fieldgroup}' deleted successfully.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    
    @login_required
    def do_upload_fieldgroup_definition_xdm(self,args:Any) -> None:
        """Upload a field group definition from a JSON XDM file"""
        parser = argparse.ArgumentParser(prog='upload_fieldgroup_definition_xdm', add_help=True)
        parser.add_argument("xdm_path", help="Path to the field group JSON XDM file")
        parser.add_argument("-ts","--test",help="Boolean. Test upload without uploading it to AEP. It will output a JSON file. Default False. Possible values: True, False",default=False,type=str2bool)
        try:
            args = parser.parse_args(shlex.split(args))
            with open(args.xdm_path, 'r') as f:
                xdm_data = json.load(f)
            myfg = fieldgroupmanager.FieldGroupManager(xdm_data,config=self.config)
            if args.test:
                data = myfg.to_dict()
                with open(f"test_{myfg.title}_fieldgroup.json", 'w') as f:
                    json.dump(data, f, indent=4)
                console.print(f"Field Group definition test exported to test_{myfg.title}_fieldgroup.json", style="green")
                console.print_json(data=data)
                return
            res = myfg.createFieldGroup()
            console.print(f"Field Group uploaded with ID: {res.get('meta:altId')}", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
        
    @login_required
    def do_get_datasets(self, args:Any) -> None:
        """List all datasets in the current sandbox"""
        parser = argparse.ArgumentParser(prog='get_datasets', add_help=True)
        parser.add_argument("-f","--filter",help="filter the dataset return by name (non-case sensitive and partial match)",type=str,default="")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            if args.filter != "":
                datasets = [ds for ds in datasets if args.filter.lower() in ds['name'].lower()]
            df_datasets = pd.DataFrame(datasets)
            df_datasets.to_csv(f"{self.config.sandbox}_datasets.csv",index=False)
            table = Table(title=f"Datasets in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="white")
            table.add_column("Name", style="white",no_wrap=True)
            table.add_column("Created At", style="yellow")
            table.add_column("Data Ingested", style="magenta")
            table.add_column("Data Type", style="red")
            for ds in datasets:
                table.add_row(
                    ds.get("id","N/A"),
                    ds.get("name","N/A"),
                    datetime.fromtimestamp(ds.get("created",1000)/1000).isoformat().split('T')[0],
                    str(ds.get("dataIngested",False)),
                    ds.get('classification').get('dataBehavior','N/A'),
                )
            console.print(table)
            console.print(f"Datasets exported to {self.config.sandbox}_datasets.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_dataset(self,args:Any) -> None:
        """Get a dataset by exact name or ID and export dataset_<id>.json."""
        parser = argparse.ArgumentParser(prog='get_dataset',add_help=True)
        parser.add_argument('dataset',help='dataset name or id', type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            if args.dataset in [d['id'] for d in datasets]:
                datasetId = next(d['id'] for d in datasets if d['id'] == args.dataset)

            elif args.dataset in [d['name'] for d in datasets]:
                datasetId = next(d['id'] for d in datasets if d['name'] == args.dataset)
            else:
                console.print(f"(!) Dataset {args.dataset} not found", style="red")
                return
            dataset = aepp_cat.getDataSet(datasetId)
            if not isinstance(dataset, dict) or datasetId not in dataset:
                raise ValueError(f"Dataset retrieval failed: {dataset}")
            console.print_json(data=dataset)
            with open(f'dataset_{datasetId}.json', 'w') as f:
                json.dump(dataset,f,indent=2)
            console.print(f"Dataset definition exported to dataset_{datasetId}.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
            return
        except SystemExit:
            return
    
    @login_required
    def do_get_datasets_tablenames(self, args:Any) -> None:
        """List all datasets with their table names in the current sandbox"""
        parser = argparse.ArgumentParser(prog='get_datasets_tablenames', add_help=True)
        parser.add_argument("-f","--filter",help="filter the dataset return by name (non-case sensitive and partial match)",type=str,default="")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            if args.filter != "":
                datasets = [ds for ds in datasets if args.filter.lower() in ds['name'].lower()]
            table = Table(title=f"Datasets in Sandbox: {self.config.sandbox}")
            table.add_column("Name", style="white")
            table.add_column("Table Name", style="cyan",no_wrap=True)
            table.add_column("Data Type", style="red")
            for ds in datasets:
                table.add_row(
                    ds.get("name","N/A"),
                    ds.get('tags',{}).get('adobe/pqs/table',["N/A"])[0],
                    ds.get('classification').get('dataBehavior','N/A'),
                )
            console.print(table)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
        
    @login_required
    def do_get_observable_schema_json(self,args:Any) -> None:
        """Get the observable schema for a dataset by name or ID"""
        parser = argparse.ArgumentParser(prog='get_observable_schema', add_help=True)
        parser.add_argument("dataset", help="Dataset ID or Dataset Name to retrieve observable schema for",type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            for ds in datasets:
                if ds.get("name","") == args.dataset or ds.get("id","") == args.dataset:
                    datasetId = ds.get("id")
            schema_json = aepp_cat.getDataSetObservableSchema(datasetId=datasetId,appendDatasetInfo=True)
            myObs = catalog.ObservableSchemaManager(schema_json)
            data = myObs.to_dict()
            with open(f"{args.dataset}_observable_schema.json", 'w') as f:
                json.dump(data, f, indent=4)
            console.print(f"Saved Observable schema to {args.dataset}_observable_schema.json.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_observable_schema_csv(self,args:Any) -> None:
        """Get the observable schema for a dataset by name or ID"""
        parser = argparse.ArgumentParser(prog='get_observable_schema', add_help=True)
        parser.add_argument("dataset", help="Dataset ID or Dataset Name to retrieve observable schema for",type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            for ds in datasets:
                if ds.get("name","") == args.dataset or ds.get("id","") == args.dataset:
                    datasetId = ds.get("id")
            schema_json = aepp_cat.getDataSetObservableSchema(datasetId=datasetId,appendDatasetInfo=True)
            myObs = catalog.ObservableSchemaManager(schema_json)
            data = myObs.to_dataframe()
            data.to_csv(f"{args.dataset}_observable_schema.csv", index=False)
            console.print(f"Saved Observable schema to {args.dataset}_observable_schema.csv.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_datasets_infos(self, args:Any) -> None:
        """List all datasets in the current sandbox"""
        parser = argparse.ArgumentParser(prog='get_datasets_infos', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets()
            aepp_cat.data.infos = aepp_cat.data.infos.sort_values(by=['ups_storageSize','datalake_storageSize'], ascending=False)
            aepp_cat.data.infos.to_csv(f"{aepp_cat.sandbox}_datasets_infos.csv",index=False)
            table = Table(title=f"Datasets in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="white")
            table.add_column("Name", style="white",no_wrap=True)
            table.add_column("UPS Rows", style="cyan")
            table.add_column("UPS Storage Size", style="green")
            table.add_column("Datalake Rows", style="magenta")
            table.add_column("Datalake Storage Size", style="yellow")
            for _, ds in aepp_cat.data.infos.iterrows():
                table.add_row(
                    ds.get("id","N/A"),
                    ds.get("name","N/A"),
                    str(ds.get("ups_rows","N/A")),
                    str(ds.get("ups_storageSize","N/A")),
                    str(ds.get("datalake_rows","N/A")),
                    str(ds.get("datalake_storageSize","N/A")),
                )
            console.print(table)
            console.print(f"Datasets infos exported to {aepp_cat.sandbox}_datasets_infos.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_dataset_expiration(self, args:Any) -> None:
        """Get the TTL (Time To Live) for datasets in the current sandbox. ONLY WORKS ON Experience Event Datasets"""
        parser = argparse.ArgumentParser(prog='get_dataset_expiration', add_help=True)
        parser.add_argument("dataset", help="Dataset ID or Dataset Name to retrieve TTL for",type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            datasetId = None
            for ds in datasets:
                if ds.get("name","") == args.dataset or ds.get("id","") == args.dataset:
                    datasetId = ds.get("id")
                    break
            if not datasetId:
                raise ValueError(f"Dataset '{args.dataset}' not found")
            ttl_info = aepp_cat.getDataSetExpiration(datasetId)
            console.print(ttl_info, style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_set_dataset_expiration(self,args:Any)->None:
        """Set the TTL (Time To Live) for a dataset in the current sandbox. ONLY WORKS ON Experience Event Datasets"""
        parser = argparse.ArgumentParser(prog='set_dataset_expiration', add_help=True)
        parser.add_argument("dataset", help="Dataset ID or Dataset Name to set TTL for",type=str)
        parser.add_argument("-t", "--ttl", help="TTL value in days",type=int)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            datasetId = None
            for ds in datasets:
                if ds.get("name","") == args.dataset or ds.get("id","") == args.dataset:
                    datasetId = ds.get("id")
                    break
            if not datasetId:
                raise ValueError(f"Dataset '{args.dataset}' not found")
            aepp_cat.getDataSetExpiration(datasetId, args.ttl)
            console.print(f"TTL for dataset '{args.dataset}' set to {args.ttl} days", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_snapshot_datasets(self,args:Any) -> None:
        """List all snapshot datasets in the current sandbox"""
        parser = argparse.ArgumentParser(prog='get_snapshot_datasets', add_help=True)
        parser.add_argument(
            "-d", "--defaultOnly",
            help="Only return datasets with the default merge policy (optional True/False; default False)",
            nargs="?", const=True, default=False, type=str2bool, metavar="BOOL",
        )
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getProfileSnapshotDatasets(explicitMergePolicy=True,flatten=True,defaultOnly=args.defaultOnly)
            df_datasets = pd.DataFrame(datasets)
            df_datasets.to_csv(f"{self.config.sandbox}_snapshot_datasets.csv",index=False)
            table = Table(title=f"Snapshot Datasets in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="white")
            table.add_column("Table Name", style="white")
            table.add_column("Merge Policy Name", style="yellow")
            table.add_column("Merge Policy ID", style="green")
            table.add_column("Default Policy", style="red")
            table.add_column("Row Count", style="white")
            for ds in datasets:
                table.add_row(
                    ds.get("id","N/A"),
                    ds.get("tags",{}).get('adobe/pqs/table',["N/A"])[0],
                    ds.get('mergePolicyName','N/A'),
                    [el.split(':')[1] for el in ds.get('tags',{}).get('unifiedProfile',[]) if el.startswith('mergePolicyId')][0],
                    "[green]True[/green]" if ds.get('defaultPolicy', False) else "[red]False[/red]",
                    str(ds.get('extensions', {}).get('adobe_lakeHouse', {}).get('metrics', {}).get('rowCount', 'N/A'))
                )
            console.print(table)
            console.print(f"Snapshot Datasets exported to {self.config.sandbox}_snapshot_datasets.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_createDataset(self, args:Any) -> None:
        """Create a new dataset in the current sandbox"""
        parser = argparse.ArgumentParser(prog='createDataset', add_help=True)
        parser.add_argument("dataset_name", help="Name of the dataset to create")
        parser.add_argument("schema_id", help="Schema ID to associate with the dataset")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config,region=args.region)
            dataset_id = aepp_cat.createDataSet(dataset_name=args.dataset_name,schemaId=args.schema_id)
            console.print(f"Dataset '{args.dataset_name}' created with ID: {dataset_id[0]}", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_enable_dataset_for_ups(self, args:Any) -> None:
        """Enable a dataset for Profile"""
        parser = argparse.ArgumentParser(prog='enable_dataset_for_profile', add_help=True)
        parser.add_argument("dataset", help="Dataset ID or Dataset Name to enable for Profile")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            for ds in datasets:
                if ds.get("name","") == args.dataset or ds.get("id","") == args.dataset:
                    datasetId = ds.get("id")
            result = aepp_cat.enableDatasetProfile(datasetId=datasetId)
            console.print(f"Dataset '{datasetId}' enabled for Profile.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_enable_dataset_for_uis(self, args:Any) -> None:
        """Enable a dataset for Unified Identity Service"""
        parser = argparse.ArgumentParser(prog='enable_dataset_for_uis', add_help=True)
        parser.add_argument("dataset", help="Dataset ID or Dataset Name to enable for UIS")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            for ds in datasets:
                if ds.get("name","") == args.dataset or ds.get("id","") == args.dataset:
                    datasetId = ds.get("id")
            result = aepp_cat.enableDatasetIdentity(datasetId=datasetId)
            console.print(f"Dataset '{datasetId}' enabled for UIS.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_enable_dataset(self,args:Any) -> None:
        """Enable a dataset for Profile and Unified Identity Service"""
        parser = argparse.ArgumentParser(prog='enable_dataset', add_help=True)
        parser.add_argument("dataset", help="Dataset ID or Dataset Name to enable")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            for ds in datasets:
                if ds.get("name","") == args.dataset or ds.get("id","") == args.dataset:
                    datasetId = ds.get("id")
            enableDatasetForUISBody = [
                { "op": "add", "path": "/tags/unifiedProfile", "value": ["enabled:true"] },
                { "op": "add", "path": "/tags/unifiedIdentity", "value": ["enabled:true"] }
            ]
            res = aepp_cat.patchDataset(datasetId=datasetId,data=enableDatasetForUISBody)
            console.print(f"Dataset '{datasetId}' enabled for Profile and UIS.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required 
    def do_get_identities(self, args:Any) -> None:
        """List all identities in the current sandbox"""
        parser = argparse.ArgumentParser(prog='get_identities', add_help=True)
        parser.add_argument("-r","--region", help="Region to get identities from: 'ndl2' (default), 'va7', 'aus5', 'can2', 'ind2'", default='ndl2',type=str)
        parser.add_argument("-co","--custom_only",help="Get only custom identities", default=False,type=str2bool)
        try:
            args = parser.parse_args(shlex.split(args))
            region = args.region if args.region else 'ndl2'
            aepp_identity = identity.Identity(config=self.config,region=args.region)
            identities = aepp_identity.getIdentities(only_custom=args.custom_only)
            df_identites = pd.DataFrame(identities)
            df_identites.to_csv(f"{self.config.sandbox}_identities.csv",index=False)
            table = Table(title=f"Identities in Sandbox: {self.config.sandbox}")
            table.add_column("Code", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("id", style="white")
            table.add_column("namespaceType", style="green")
            for _, iden in df_identites.iterrows():
                table.add_row(
                    iden.get("code","N/A"),
                    iden.get("name","N/A"),
                    str(iden.get("id","N/A")),
                    iden.get("namespaceType","N/A"),
                )
            console.print(table)
            console.print(f"Identities exported to {self.config.sandbox}_identities.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_create_identity(self,args:Any) -> None:
        """Create a new identity namespace"""
        parser = argparse.ArgumentParser(prog='create_identity', add_help=True)
        parser.add_argument("-c","--code", help="Code for the new identity namespace (e.g., email, phone)")
        parser.add_argument("-n","--name", help="Display name for the new identity namespace")
        parser.add_argument("-t","--type", help="Type for the new identity namespace. Possible Values: COOKIE, CROSS_DEVICE, DEVICE, EMAIL, MOBILE, NON_PEOPLE or PHONE")
        parser.add_argument("-d","--description", help="Description for the new identity namespace", default="", type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_identity = identity.Identity(config=self.config)
            if args.type not in ["COOKIE", "CROSS_DEVICE", "DEVICE", "EMAIL", "MOBILE", "NON_PEOPLE", "PHONE"]:
                console.print(f"(!) Error: Invalid identity type '{args.type}'. Must be one of: COOKIE, CROSS_DEVICE, DEVICE, EMAIL, MOBILE, NON_PEOPLE, PHONE", style="red")
                return
            new_identity = aepp_identity.createIdentity(code=args.code,name=args.name,idType=args.type,description=args.description)
            if 'code' in new_identity.keys() and 'status' in new_identity.keys():
                console.print_json(data=new_identity, style="green")
            else:
                console.print_json(data=new_identity,style='orange_red1')
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_audiences(self, args:Any) -> None:
        """List all audiences in the current sandbox. If fails, it will use the segments API as fallback."""
        parser = argparse.ArgumentParser(prog='get_audiences', add_help=True)
        parser.add_argument("-f","--filter",help="filter the audience return by name (non-case sensitive and partial match)",type=str,default="")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_audience = segmentation.Segmentation(config=self.config)
            try:
                audiences = aepp_audience.getAudiences()
            except Exception as e:
                console.print(f"Issue with audience retrieval: {str(e)}", style="yellow")
                console.print(f"using getSegments method.", style="yellow")
                console.print(f"external audiences will not be available in reports", style="yellow")
                audiences = aepp_audience.getSegments()
            if args.filter != "":
                audiences = [aud for aud in audiences if args.filter.lower() in aud['name'].lower()]
            flw = flowservice.FlowService(config=self.config)
            destinations = flw.getFlows(onlyDestinations=True)
            segments_shared = []
            for tmpFlow in destinations:
                if len(tmpFlow['transformations'])>0:
                    tmpSegmentShared = tmpFlow['transformations'][0].get('params',{}).get('segmentSelectors',{}).get('selectors',[])
                    for s in tmpSegmentShared:
                        s['flowId'] = tmpFlow['id']
                    segments_shared += tmpSegmentShared
            segment_shared_dict = {}
            for seg in segments_shared:
                segId = seg.get('value',{}).get('id')
                if segId is None:
                    continue
                scheduleEnd = seg.get('value',{}).get('schedule',{}).get('endDate')
                entry = {
                    "exportMode" : seg.get('value',{}).get('exportMode'),
                    "scheduleFrequency": seg.get('value',{}).get("schedule",{}).get('frequency',''),
                    "flowId" : seg["flowId"],
                    "scheduleEnd": scheduleEnd
                }
                existing = segment_shared_dict.get(segId)
                if existing is None:
                    segment_shared_dict[segId] = entry
                    continue
                if scheduleEnd is None:
                    segment_shared_dict[segId] = entry
                    continue
                else:
                    existingEnd = existing.get("scheduleEnd")
                    if existingEnd is not None:
                        try:
                            if datetime.fromisoformat(scheduleEnd) > datetime.fromisoformat(existingEnd):
                                segment_shared_dict[segId] = entry
                        except ValueError:
                            pass
            dateNow = datetime.now()
            for aud in audiences:
                aud['usedInFlow'] = True if segment_shared_dict.get(aud.get("id","N/A"),{}) != {} else False
                if aud['usedInFlow']:
                    scheduleEnd = segment_shared_dict.get(aud.get("id","N/A"),{}).get("scheduleEnd")
                    if scheduleEnd:
                        try:
                            aud['activeInFlow'] = dateNow < datetime.fromisoformat(scheduleEnd)
                        except ValueError:
                            aud['activeInFlow'] = True
                    else:
                        aud['activeInFlow'] = True
                else:
                    aud['activeInFlow'] = '-'
                aud['sharedInfo'] = segment_shared_dict.get(aud.get("id","N/A"),{})
            df_audiences = pd.DataFrame(audiences)
            df_audiences.to_csv(f"{self.config.sandbox}_audiences.csv",index=False)   
            table = Table(title=f"Audiences in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Evaluation", style="yellow")
            table.add_column("Total Profiles", style="green")
            table.add_column("In Flow", style="white")
            table.add_column("Active in Flow", style="white")
            for aud in audiences:
                table.add_row(
                    aud.get("id","N/A"),
                    aud.get("name","N/A"),
                    '[bright_blue]Batch[/bright_blue]' if aud.get("evaluationInfo",{}).get("batch",{}).get('enabled') else '[chartreuse1]Streaming[/chartreuse1]' if aud.get("evaluationInfo",{}).get("continuous",{}).get('enabled') else '[purple]Edge[/purple]' if aud.get("evaluationInfo",{}).get("synchronous",{}).get('enabled') else 'N/A',
                    str(aud.get('metrics',{}).get('data',{}).get('totalProfiles','N/A')),
                    '[green3]True[/green3]' if aud.get("usedInFlow",False) else '[red3]False[/red3]',
                    '[green3]True[/green3]' if aud.get("activeInFlow",False) == True else ('[red3]False[/red3]' if aud.get("activeInFlow") == False else "-"),
                )
            console.print(table)
            console.print(f"Audiences exported to {self.config.sandbox}_audiences.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_create_audiences_job(self,args:Any)->None:
        """
        Create a job for audience segmentation. Only 50 jobs available per year for production sandboxes.
        Arguments:
            audience_ids : list of audience IDs such as "audienceId1" "audienceId2" "audienceId3"
        """
        parser = argparse.ArgumentParser(prog="create_audiences_jobs",description='Create an audience Job for the audience ID provided',add_help=True)
        parser.add_argument("audience_ids",type='str',nargs="+")
        try:
            from aepp import segmentation
            args = parser.parse_args(shlex.split(args))
            seg = segmentation.Segmentation(config = self.config)
            res = seg.createJob(segmentIds=args)
            console.print_json(res)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
        
    @login_required
    def do_get_batch_evaluation(self,args:Any)->None:
        """
        Get the batch evaluation job definition for the sandbox.
        """
        try:
            from aepp import segmentation
            seg = segmentation.Segmentation(config = self.config)
            activeJobs = seg.getSchedules()
            batchSegmentationJob = [job for job in activeJobs if job.get('type') == 'batch_segmentation' and job.get('frequency') == 'daily']
            if len(batchSegmentationJob) == 0:
                console.print("No batch segmentation job found.", style="yellow")
            else:
                console.print_json(data=batchSegmentationJob[0])
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_update_batch_evaluation_time(self,args:Any)->None:
        """
        Update the batch evaluation time for the sandbox.
        Arguments:
            schedule : the schedule to update (ex: "0 0 1 * * ?" for daily at 1am)
        """
        parser = argparse.ArgumentParser(prog="update_batch_evaluation_time",description='Update the batch evaluation time for the sandbox',add_help=True)
        parser.add_argument("schedule",type=str,help="the schedule to update (ex: \"0 0 1 * * ?\" for daily at 1am)")
        try:
            from aepp import segmentation
            args = parser.parse_args(shlex.split(args))
            seg = segmentation.Segmentation(config = self.config)
            res = seg.updateScheduledBatchSegmentationJob(schedule=args.schedule)
            console.print(f"Sandbox '{self.sandbox}' batch evaluation job updated successfully.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_flexible_audience_evaluation(self,args:Any)->None:
        """
        Create a flexible audience evaluation job for the sandbox.
        Arguments:
            audienceIds : list of audience IDs such as "audienceId1" "audienceId2" "audienceId3"
        """
        parser = argparse.ArgumentParser(prog="flexible_audience_evaluation",description='Create a flexible audience evaluation job for the sandbox',add_help=True)
        parser.add_argument("audience_ids",help="list of audience IDs such as 'audienceId1' 'audienceId2' 'audienceId3'",type=str,nargs="+")
        try:
            from aepp import segmentation
            args = parser.parse_args(shlex.split(args))
            seg = segmentation.Segmentation(config = self.config)
            res = seg.createJob(segmentIds=args.audience_ids)
            console.print_json(data=res)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_extract_audience_paths(self,args:Any)->None:
        """
        Get the list of paths used in audience definitions.
        """
        parser = argparse.ArgumentParser(prog="extract_audience_paths",description='Get the list of paths used in audience definitions',add_help=True)
        parser.add_argument("audience",description="Audience ID or audience name to get paths for",type=str)
        parser.add_argument("-r","--recursive",help="Boolean. Get paths recursively from segment references. Default False. Possible values: True, False",default=False,type=str2bool)
        try:
            from aepp import segmentation
            seg = segmentation.Segmentation(config = self.config)
            args = parser.parse_args(shlex.split(args))
            audiences = seg.getAudiences()
            audience = next((aud for aud in audiences if aud.get("id") == args.audience or args.audience in aud.get("name", "")), None)
            if not audience:
                console.print(f"Audience '{args.audience}' not found.", style="red")
                return
            list_paths:list = seg.extractPaths(audience, recursive=args.recursive)
            with open(f"audience_{audience.get('id')}_paths.json", 'w', newline='') as jsonfile:
                json.dump(list_paths, jsonfile, indent=4)
            console.print_json(data=list_paths)
            console.print(f"Audience paths exported to audience_{audience.get('id')}_paths.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_extract_audience_ref(self,args:Any)->None:
        """
        Get the list of audience references used in audience definitions.
        """
        parser = argparse.ArgumentParser(prog="extract_audience_ref",description='Get the list of audience references used in audience definitions',add_help=True)
        parser.add_argument("audience",description="Audience ID or audience name to get references for",type=str)
        try:
            from aepp import segmentation
            seg = segmentation.Segmentation(config = self.config)
            args = parser.parse_args(shlex.split(args))
            audiences = seg.getAudiences()
            audience = next((aud for aud in audiences if aud.get("id") == args.audience or args.audience in aud.get("name", "")), None)
            if not audience:
                console.print(f"Audience '{args.audience}' not found.", style="red")
                return
            list_refs:list = seg.extractAudiences(audience)
            with open(f"audience_{audience.get('id')}_references.json", 'w', newline='') as jsonfile:
                json.dump(list_refs, jsonfile, indent=4)
            console.print_json(data=list_refs)
            console.print(f"Audience references exported to audience_{audience.get('id')}_references.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    
    @login_required
    def do_get_tags(self,args:Any)->None:
        """
        Provide the list of tags defined in the current organization
        """
        parser = argparse.ArgumentParser(prog='get_tags', add_help=True)
        try:
            from aepp import tags
            args = parser.parse_args(shlex.split(args))
            aepp_tag = tags.Tags(config=self.config)
            tags = aepp_tag.getTags()
            df_tags = pd.DataFrame(tags)
            df_tags.to_csv(f"tags.csv",index=False)
            table = Table(title=f"Tags in Organization: {self.config.org_id}")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Category Name", style="white")
            for _, tg in df_tags.iterrows():
                table.add_row(
                    str(tg.get("id","N/A")),
                    tg.get("name","N/A"),
                    tg.get("tagCategoryName","N/A"),
                )
            console.print(table)
            console.print(f"Tags exported to tags.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_flows(self, args:Any) -> None:
        """List flows in the current sandbox based on parameters provided. By default, list all sources and destinations for customers. Default time check: Last 24h."""
        parser = argparse.ArgumentParser(prog='get_flows', add_help=True)
        parser.add_argument("-i","--internal_flows",help="Boolean. Get internal flows. Default False. Possible values: True, False", default=False,type=str2bool)
        parser.add_argument("-t","--type",help="Type of flows to get. Possible values: source, destination, internal. Default: all", default="all",type=str)
        parser.add_argument("-adv","--advanced",help="Boolean. Get advanced information about runs. Default False. Possible values: True, False", default=False,type=str2bool)
        parser.add_argument("-ao","--active_only",help="Boolean. Get only active flows during that time period. Default True. Possible values: True, False", default=True,type=str2bool)
        parser.add_argument("-mn","--minutes", help="Timeframe in minutes to check for errors, default 0", default=0,type=int)
        parser.add_argument("-H","--hours", help="Timeframe in hours to check for errors, default 24", default=0,type=int)
        parser.add_argument("-d","--days", help="Timeframe in days to check for errors, default 0", default=0,type=int)
        try:
            args = parser.parse_args(shlex.split(args))
            timetotal_minutes = args.minutes + (args.hours * 60) + (args.days * 1440)
            if timetotal_minutes == 0:
                timetotal_minutes = 1440  # default to last 24 hours
            timereference = int(datetime.now().timestamp()*1000) - (timetotal_minutes * 60 * 1000)
            aepp_flow = flowservice.FlowService(config=self.config)
            flows = aepp_flow.getFlows(n_results="inf")
            runs = None
            if args.active_only:
                runs = aepp_flow.getRuns(n_results="inf",prop=[f'metrics.durationSummary.startedAtUTC>{timereference}'])
                active_flow_ids = list(set([run.get("flowId") for run in runs]))            
            source_flows = aepp_flow.getFlows(onlySources=True)
            destinations_flows = aepp_flow.getFlows(onlyDestinations=True)
            list_source_ids = [f.get("id") for f in source_flows]
            list_destination_ids = [f.get("id") for f in destinations_flows]
            if args.internal_flows or args.type == "internal":
                list_flows = flows
            else:
                if args.type == "source":
                    list_flows = source_flows
                elif args.type == "destination":
                    list_flows = destinations_flows
                else:
                    list_flows = source_flows + destinations_flows
            if args.active_only:
                list_flows = [fl for fl in list_flows if fl.get("id") in active_flow_ids]
            if args.advanced:
                if runs is None:
                    runs = aepp_flow.getRuns(n_results="inf",prop=[f'metrics.durationSummary.startedAtUTC>{timereference}'])
                runs_by_flow = {}
                for run in runs:
                    flow_id = run.get("flowId")
                    if flow_id not in runs_by_flow:
                        runs_by_flow[flow_id] = {
                            "total_runs": 0,
                            "failed_runs": 0,
                            "success_runs": 0,
                            "partial_success":0,
                        }
                    runs_by_flow[flow_id]["total_runs"] += 1
                    status = run.get("metrics",{}).get("statusSummary",{}).get("status","unknown")
                    if status == "failed":
                        runs_by_flow[flow_id]["failed_runs"] += 1
                    elif status == "success":
                        runs_by_flow[flow_id]["success_runs"] += 1
                    elif status == "partialSuccess":
                        runs_by_flow[flow_id]["partial_success"] += 1
            report_flows = []
            for fl in list_flows:
                obj = {
                    "id": fl.get("id","N/A"),
                    "name": fl.get("name","N/A"),
                    "created": fl.get("createdAt",1000),
                    "flowSpec": fl.get("flowSpec",{}).get('id','N/A'),
                    "sourceConnectionId": fl.get("sourceConnectionIds",["N/A"])[0],
                    "targetConnectionId": fl.get("targetConnectionIds",["N/A"])[0],
                    "connectionSpec": fl.get("inheritedAttributes",{}).get('sourceConnections',[{}])[0].get('connectionSpec',{}).get('id'),
                    "type": fl.get("inheritedAttributes",{}).get('properties','N/A'),
                }
                if obj.get("id") in list_source_ids:
                    obj["type"] = "Source"
                elif obj.get("id") in list_destination_ids:
                    obj["type"] = "Destination"
                else:
                    obj["type"] = "Internal"
                if fl.get('transformations') and len(fl.get('transformations')) > 0:
                    obj["Transformation"] = True
                else:
                    obj["Transformation"] = False
                if args.advanced:
                    run_info = runs_by_flow.get(obj.get("id"),{"total_runs":0,"failed_runs":0,"success_runs":0})
                    obj["Total Runs"] = run_info.get("total_runs",0)
                    obj["Failed Runs"] = run_info.get("failed_runs",0)
                    obj["Successful Runs"] = run_info.get("success_runs",0)
                    obj["Partial Success Runs"] = run_info.get("partial_success",0)
                report_flows.append(obj)
            df_flows = pd.DataFrame(list_flows)
            filename = f"{self.config.sandbox}_flows_{timereference/1000}"
            if args.advanced:
                filename = f"{filename}_advanced"
            if args.active_only == False:
                filename = f"{filename}_all"
            if args.internal_flows:
                filename = f"{filename}_internal"
            df_flows.to_csv(f"{filename}.csv",index=False)
            table = Table(title=f"Flows in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Type", style="white")
            if args.advanced == False:
                table.add_column("Created", style="white")
                table.add_column("Transformation", style="white")
                table.add_column("Flow Spec", style="white")
                table.add_column("Source Conn ID", style="white")
                table.add_column("Target Conn ID", style="white")
            if args.advanced:
                table.add_column("Total Runs", style="blue")
                table.add_column("Successful", style="green")
                table.add_column("Failed", style="red")
                table.add_column("Partial Success", style='orange1')
                table.add_column("Success Rate", style="green")
                table.add_column("Failure Rate", style="red")
                
            for fl in report_flows:
                row_data = []
                if args.advanced:
                    if fl.get("Failed Runs",0) > 0:
                        colorStart = "[red]"
                        colorEnd = "[/red]"
                    else:
                        colorStart = "[green]"
                        colorEnd = "[/green]"
                else:
                    colorStart = ""
                    colorEnd = ""
                row_data = [
                    f"{colorStart}{fl.get('id','N/A')}{colorEnd}",
                    f"{colorStart}{fl.get('name','N/A')}{colorEnd}",
                    f"{colorStart}{fl.get('type','N/A')}{colorEnd}",
                ]
                if args.advanced == False:
                    row_data.extend([
                        f"{colorStart}{datetime.fromtimestamp(fl.get('created',1000)/1000).isoformat().split('T')[0]}{colorEnd}",
                        f"{colorStart}{str(fl.get('Transformation', False))}{colorEnd}",
                        f"{colorStart}{fl.get('flowSpec','N/A')}{colorEnd}",
                        f"{colorStart}{fl.get('sourceConnectionId','N/A')}{colorEnd}",
                        f"{colorStart}{fl.get('targetConnectionId','N/A')}{colorEnd}",
                    ])
                if args.advanced:
                    total_runs = fl.get("Total Runs", 0)
                    successful_runs = fl.get("Successful Runs", 0)
                    failed_runs = fl.get("Failed Runs", 0)
                    partial_success = fl.get('Partial Success Runs',0)
                    if partial_success>0 and failed_runs==0:
                        colorStart = "[orange1]"
                        colorEnd = "[/orange1]"
                    row_data[0] = f"{colorStart}{fl.get('id','N/A')}{colorEnd}"
                    row_data[1] = f"{colorStart}{fl.get('name','N/A')}{colorEnd}"
                    row_data[2] = f"{colorStart}{fl.get('type','N/A')}{colorEnd}"
                    success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
                    failure_rate = (failed_runs / total_runs * 100) if total_runs > 0 else 0
                    row_data.extend([
                        f"{colorStart}{str(total_runs)}{colorEnd}",
                        f"{colorStart}{str(successful_runs)}{colorEnd}",
                        f"{colorStart}{str(failed_runs)}{colorEnd}",
                        f"{colorStart}{str(partial_success)}{colorEnd}",
                        f"{colorStart}{success_rate:.0f}%{colorEnd}",
                        f"{colorStart}{failure_rate:.0f}%{colorEnd}"
                    ])
                table.add_row(*row_data)
            console.print(table)
            console.print(f"Flows exported to {filename}.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_flow_errors(self,args:Any) -> None:
        """Get errors for a specific flow, saving it in a JSON file for specific timeframe, default last 24 hours."""
        parser = argparse.ArgumentParser(prog='get_flow_errors', add_help=True)
        parser.add_argument("flow_id", help="Flow ID to get errors for")
        parser.add_argument("-mn","--minutes", help="Timeframe in minutes to check for errors, default 0", default=0,type=int)
        parser.add_argument("-H","--hours", help="Timeframe in hours to check for errors, default 24", default=0,type=int)
        parser.add_argument("-d","--days", help="Timeframe in days to check for errors, default 0", default=0,type=int)
        try:
            args = parser.parse_args(shlex.split(args))
            timetotal_minutes = args.minutes + (args.hours * 60) + (args.days * 1440)
            if timetotal_minutes == 0:
                timetotal_minutes = 1440  # default to last 24 hours
            aepp_flow = flowservice.FlowService(config=self.config)
            timereference = int(datetime.now().timestamp()*1000) - (timetotal_minutes * 60 * 1000)
            failed_runs = aepp_flow.getRuns(prop=['metrics.statusSummary.status==failed',f'flowId=={args.flow_id}',f'metrics.durationSummary.startedAtUTC>{timereference}'],n_results="inf")
            with open(f"flow_{args.flow_id}_errors.json", 'w') as f:
                json.dump(failed_runs, f, indent=4)
            console.print(f"Flow errors exported to flow_{args.flow_id}_errors.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_flow_partial_success(self,args:Any) -> None:
        """Get the partial success for a specific flow, saving it in a JSON file for specific timeframe, default last 24 hours."""
        parser = argparse.ArgumentParser(prog='get_flow_partial_success', add_help=True)
        parser.add_argument("flow_id", help="Flow ID to get partial success for")
        parser.add_argument("-mn","--minutes", help="Timeframe in minutes to check for errors, default 0", default=0,type=int)
        parser.add_argument("-H","--hours", help="Timeframe in hours to check for errors, default 24", default=0,type=int)
        parser.add_argument("-d","--days", help="Timeframe in days to check for errors, default 0", default=0,type=int)
        try:
            args = parser.parse_args(shlex.split(args))
            timetotal_minutes = args.minutes + (args.hours * 60) + (args.days * 1440)
            if timetotal_minutes == 0:
                timetotal_minutes = 1440  # default to last 24 hours
            aepp_flow = flowservice.FlowService(config=self.config)
            timereference = int(datetime.now().timestamp()*1000) - (timetotal_minutes * 60 * 1000)
            failed_runs = aepp_flow.getRuns(prop=['metrics.statusSummary.status==partialSuccess',f'flowId=={args.flow_id}',f'metrics.durationSummary.startedAtUTC>{timereference}'],n_results="inf")
            with open(f"flow_{args.flow_id}_partial_success.json", 'w') as f:
                json.dump(failed_runs, f, indent=4)
            console.print(f"Flow errors exported to flow_{args.flow_id}_partial_success.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return


    @login_required
    def do_create_dataset_http_source(self,args:Any) -> None:
        """Create an HTTP Source connection for a specific dataset, for XDM compatible data only."""
        parser = argparse.ArgumentParser(prog='do_create_dataset_http_source', add_help=True)
        parser.add_argument("dataset", help="Name or ID of the Dataset Source connection to create")
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            if args.dataset in [ds.get("name","") for ds in datasets]:
                for ds in datasets:
                    if ds.get("name","") == args.dataset:
                        datasetId = ds.get("id")
            else:
                datasetId = args.dataset
            flw = flowservice.FlowService(config=self.config)
            res = flw.createFlowStreaming(datasetId=datasetId)
            console.print(f"HTTP Source connection created with Flow ID: {res.get('flow',{}).get('id')}", style="green")
            source_id = res.get('source_connection_id',{}).get('id')
            sourceConnection = flw.getSourceConnection(sourceConnectionId=source_id)
            console.print(f"Endpoint URL: {sourceConnection.get('params',{}).get('inletUrl')}", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_DLZ_credential(self,args:Any) -> None:
        """Get Data Lake Zone credential for the current sandbox. By default, it retrieves the 'user_drop_zone' credential, but you can specify 'dlz_destination' to get the credential for the DLZ destination connection."""
        parser = argparse.ArgumentParser(prog='get_DLZ_credential', add_help=True)
        parser.add_argument("type",nargs='?',help="Type of credential to retrieve: 'user_drop_zone' or 'dlz_destination'",default="user_drop_zone")
        try:
            args = parser.parse_args(shlex.split(args))
            flw = flowservice.FlowService(config=self.config)
            cred = flw.getLandingZoneCredential(dlz_type=args.type)
            console.print(f"Data Landing Zone Credential '{args.type}' for sandbox '{self.config.sandbox}':", style="green")
            console.print_json(data=cred)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_delete_dataset(self, args:Any) -> None:
        """Delete a dataset from the current sandbox. This is a destructive, irreversible operation - use with caution."""
        parser = argparse.ArgumentParser(prog='delete_dataset', add_help=True)
        parser.add_argument("dataset", help="Dataset name or ID to delete")
        parser.add_argument("-a","--associated_artifacts",help="Boolean. Also delete the associated dataflows and schema. Default False.",type=str2bool,default=False)
        parser.add_argument("-y","--yes",help="Boolean. Skip the confirmation prompt. Default False.",type=str2bool,default=False)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
            dataset = next((ds for ds in datasets if ds.get("name") == args.dataset or ds.get("id") == args.dataset), None)
            if dataset is None:
                console.print(f"(!) Dataset '{args.dataset}' not found.", style="red")
                return
            datasetId = dataset.get("id")
            schemaRef = dataset.get('schemaRef',{}).get('id')
            warnings = [f"Dataset ID: {datasetId}"]
            if dataset.get("dataIngested"):
                warnings.append("[bold yellow]This dataset has ingested data - deleting it permanently removes that data.[/bold yellow]")
            if args.associated_artifacts:
                aepp_flow = flowservice.FlowService(config=self.config)
                target_dataflows = aepp_flow.getTargetConnections()
                source_dataflows = aepp_flow.getSourceConnections()
                list_target_ids = [fl['id'] for fl in target_dataflows if fl.get('params',{}).get('dataSetId') == datasetId]
                list_source_datalake = [fl for fl in source_dataflows if fl.get('name') == 'Datalake Source Connection']
                list_source_ids = [fl['id'] for fl in list_source_datalake if fl.get('params',{}).get('dataSetId') == datasetId]
                flows = aepp_flow.getFlows()
                impacted_flows = [f for f in flows if f.get('sourceConnectionIds',[""])[0] in list_source_ids or f.get('targetConnectionIds',[""])[0] in list_target_ids]
                connection_count = sum(len(f.get('sourceConnectionIds',[])) + len(f.get('targetConnectionIds',[])) for f in impacted_flows)
                if impacted_flows:
                    names = ", ".join(f.get('name','N/A') for f in impacted_flows)
                    warnings.append(f"[bold red]{len(impacted_flows)} dataflow(s) will also be deleted (+ {connection_count} connection(s)):[/bold red] {names}")
                fg_count, dt_count = 0, 0
                if schemaRef:
                    try:
                        schemaManager = schemamanager.SchemaManager(schemaRef, config=self.config)
                        fg_count = len(schemaManager.fieldGroups)
                        dt_ids = set()
                        for fieldgroupId, fieldgroupName in schemaManager.fieldGroups.items():
                            myFG = schemaManager.getFieldGroupManager(fieldgroupName)
                            dt_ids.update(myFG.dataTypes.keys())
                        dt_count = len(dt_ids)
                    except Exception:
                        pass
                    detail = f" (+ {fg_count} field group(s), {dt_count} data type(s))" if (fg_count or dt_count) else ""
                    warnings.append(f"[bold red]Associated schema will also be deleted:[/bold red] {schemaRef}{detail}")
                summary_bits = ["1 dataset"]
                if impacted_flows:
                    summary_bits.append(f"{len(impacted_flows)} dataflow(s)")
                if connection_count:
                    summary_bits.append(f"{connection_count} connection(s)")
                if schemaRef:
                    summary_bits.append("1 schema")
                if fg_count:
                    summary_bits.append(f"{fg_count} field group(s)")
                if dt_count:
                    summary_bits.append(f"{dt_count} data type(s)")
                warnings.append(f"[bold red]Summary: this will permanently delete {' + '.join(summary_bits)}.[/bold red]")
            else:
                warnings.append("Associated dataflows and schema will be left untouched (pass -a true to cascade).")
            warnings.append("[bold red]This action is irreversible.[/bold red]")
            if not self._confirm_destructive("delete dataset", dataset.get('name'), warnings, args.yes):
                return
            deleter = deletion.Deletion(config=self.config)
            res = deleter.deleteDataset(datasetId=datasetId, associatedArtifacts=args.associated_artifacts)
            console.print_json(data=res)
            console.print(f"Dataset '{dataset.get('name')}' deletion completed.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_delete_schema(self, args:Any) -> None:
        """Delete a schema from the current sandbox. This is a destructive, irreversible operation - use with caution."""
        parser = argparse.ArgumentParser(prog='delete_schema', add_help=True)
        parser.add_argument("schema", help="Schema title, $id or alt:Id to delete")
        parser.add_argument("-a","--associated_artifacts",help="Boolean. Also delete the field groups and data types used exclusively by this schema. Default False.",type=str2bool,default=False)
        parser.add_argument("-y","--yes",help="Boolean. Skip the confirmation prompt. Default False.",type=str2bool,default=False)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            schemas = aepp_schema.getSchemas()
            if args.schema in aepp_schema.data.schemas_altId.keys():
                schemaId = aepp_schema.data.schemas_altId[args.schema]
            else:
                schemaId = args.schema
            schema_info = next((sc for sc in schemas if sc.get('$id') == schemaId or sc.get('meta:altId') == schemaId), None)
            if schema_info is None:
                console.print(f"(!) Schema '{args.schema}' not found.", style="red")
                return
            warnings = [f"Schema ID: {schema_info.get('meta:altId')}"]
            if args.associated_artifacts:
                schemaManager = schemamanager.SchemaManager(schemaId, config=self.config)
                fg_names = list(schemaManager.fieldGroups.values())
                dt_all_ids = set()
                if fg_names:
                    warnings.append(f"[bold red]{len(fg_names)} field group(s) will also be deleted:[/bold red] {', '.join(fg_names)}")
                    for fieldgroupId, fieldgroupName in schemaManager.fieldGroups.items():
                        myFG = schemaManager.getFieldGroupManager(fieldgroupName)
                        dt_names = list(myFG.dataTypes.values())
                        dt_all_ids.update(myFG.dataTypes.keys())
                        if dt_names:
                            warnings.append(f"  [bold red]Data type(s) used by '{fieldgroupName}' that will also be deleted:[/bold red] {', '.join(dt_names)}")
                summary_bits = ["1 schema"]
                if fg_names:
                    summary_bits.append(f"{len(fg_names)} field group(s)")
                if dt_all_ids:
                    summary_bits.append(f"{len(dt_all_ids)} data type(s)")
                warnings.append(f"[bold red]Summary: this will permanently delete {' + '.join(summary_bits)}.[/bold red]")
            else:
                warnings.append("Associated field groups and data types will be left untouched (pass -a true to cascade).")
            warnings.append("[bold yellow]Deletion will fail if the schema is still enabled for Profile/Identity, or referenced by a dataset.[/bold yellow]")
            warnings.append("[bold red]This action is irreversible.[/bold red]")
            if not self._confirm_destructive("delete schema", schema_info.get('title'), warnings, args.yes):
                return
            deleter = deletion.Deletion(config=self.config)
            res = deleter.deleteSchema(schemaId=schemaId, associatedArtifacts=args.associated_artifacts)
            console.print_json(data=res)
            console.print(f"Schema '{schema_info.get('title')}' deletion completed.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_delete_dataflow(self, args:Any) -> None:
        """Delete a dataflow from the current sandbox. This is a destructive, irreversible operation - use with caution."""
        parser = argparse.ArgumentParser(prog='delete_dataflow', add_help=True)
        parser.add_argument("flow", help="Dataflow name or ID to delete")
        parser.add_argument("-a","--associated_artifacts",help="Boolean. Also delete the associated source and target connections. Default False.",type=str2bool,default=False)
        parser.add_argument("-y","--yes",help="Boolean. Skip the confirmation prompt. Default False.",type=str2bool,default=False)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_flow = flowservice.FlowService(config=self.config)
            flows = aepp_flow.getFlows()
            flow_info = next((f for f in flows if f.get("name") == args.flow or f.get("id") == args.flow), None)
            if flow_info is None:
                console.print(f"(!) Dataflow '{args.flow}' not found.", style="red")
                return
            flowId = flow_info.get("id")
            source_ids = flow_info.get('sourceConnectionIds',[])
            target_ids = flow_info.get('targetConnectionIds',[])
            warnings = [f"Dataflow ID: {flowId}"]
            if args.associated_artifacts:
                if source_ids:
                    warnings.append(f"[bold red]{len(source_ids)} source connection(s) will also be deleted:[/bold red] {', '.join(source_ids)}")
                if target_ids:
                    warnings.append(f"[bold red]{len(target_ids)} target connection(s) will also be deleted:[/bold red] {', '.join(target_ids)}")
                total_conn = len(source_ids) + len(target_ids)
                summary_bits = ["1 dataflow"]
                if total_conn:
                    summary_bits.append(f"{total_conn} connection(s)")
                warnings.append(f"[bold red]Summary: this will permanently delete {' + '.join(summary_bits)}.[/bold red]")
            else:
                warnings.append("Source and target connections will be left untouched (pass -a true to cascade).")
            base_conn = flow_info.get('inheritedAttributes',{}).get('sourceConnections',[{}])[0].get('baseConnection',{}).get('id')
            if base_conn:
                warnings.append(f"Base connection {base_conn} will [italic]not[/italic] be deleted (it may be shared by other dataflows).")
            warnings.append("[bold yellow]Any ingestion or activation currently relying on this dataflow will stop immediately.[/bold yellow]")
            warnings.append("[bold red]This action is irreversible.[/bold red]")
            if not self._confirm_destructive("delete dataflow", flow_info.get('name'), warnings, args.yes):
                return
            deleter = deletion.Deletion(config=self.config)
            res = deleter.deleteDataFlow(flowId=flowId, associatedArtifacts=args.associated_artifacts)
            console.print_json(data=res)
            console.print(f"Dataflow '{flow_info.get('name')}' deletion completed.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_delete_audience(self, args:Any) -> None:
        """Delete an audience/segment from the current sandbox. This is a destructive, irreversible operation - use with caution."""
        parser = argparse.ArgumentParser(prog='delete_audience', add_help=True)
        parser.add_argument("audience", help="Audience name or ID to delete")
        parser.add_argument("-y","--yes",help="Boolean. Skip the confirmation prompt. Default False.",type=str2bool,default=False)
        parser.add_argument("-w","--waittime",help="Seconds to wait for destination flow updates to propagate before deleting. Default 30.",type=int,default=30)
        try:
            args = parser.parse_args(shlex.split(args))
            seg = segmentation.Segmentation(config=self.config)
            try:
                audiences = seg.getAudiences()
            except Exception:
                audiences = seg.getSegments()
            audience = next((aud for aud in audiences if aud.get("id") == args.audience or aud.get("name") == args.audience), None)
            if audience is None:
                console.print(f"(!) Audience '{args.audience}' not found.", style="red")
                return
            audienceId = audience.get("id")
            warnings = [f"Audience ID: {audienceId}"]
            aepp_flow = flowservice.FlowService(config=self.config)
            destination_flows = aepp_flow.getFlows(onlyDestinations=True)
            impacted_flows = []
            for flow in destination_flows:
                try:
                    selectors = flow['transformations'][0]['params']['segmentSelectors']['selectors']
                except (KeyError, IndexError):
                    continue
                if audienceId in [s.get('value',{}).get('id') for s in selectors]:
                    impacted_flows.append({"id": flow.get("id","N/A"), "name": flow.get("name","N/A")})
            if impacted_flows:
                console.print(f"(!) Audience '{audience.get('name')}' is activated to the following destination(s). It will be removed from each before deletion:", style="bold red")
                table = Table(title="Impacted Destination Flows")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="magenta")
                for f in impacted_flows:
                    table.add_row(f["id"], f["name"])
                console.print(table)
                warnings.append(f"[bold red]{len(impacted_flows)} destination(s) will be updated to remove this audience (see table above).[/bold red]")
                warnings.append(f"The deletion will wait {args.waittime}s after updating those destinations before removing the audience.")
            warnings.append("[bold yellow]Any active exports/activations built on this audience will stop receiving updates.[/bold yellow]")
            warnings.append("[bold red]This action is irreversible.[/bold red]")
            if not self._confirm_destructive("delete audience", audience.get('name'), warnings, args.yes):
                return
            deleter = deletion.Deletion(config=self.config)
            res = deleter.deleteAudience(audienceId=audienceId, waittime=args.waittime)
            console.print_json(data=res)
            console.print(f"Audience '{audience.get('name')}' deletion completed.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_queries(self, args:Any)-> None:
        """List top 1000 queries in the current sandbox for the last 24 hours by default, optionally filtered by dataset ID. Display top 10 in console and export all to a CSV file."""
        parser = argparse.ArgumentParser(prog='get_queries', add_help=True)
        parser.add_argument("-ds","--dataset", help="Dataset ID to filter queries", default=None)
        state_aliases = {"running": "IN_PROGRESS", "completed": "SUCCESS", "failed": "FAILED"}
        states = ("SUBMITTED", "IN_PROGRESS", "SUCCESS", "FAILED", "KILLED", "TIMEOUT")
        parser.add_argument("-st","--state", help="API state or alias: running, completed, failed", default=None,
                            type=lambda value: state_aliases.get(value.lower(), value.upper()), choices=states)
        parser.add_argument("-H","--hours", help="Lookback window in hours, default 0", default=0,type=int)
        parser.add_argument("-d","--days", help="Lookback window in days, default 0", default=0,type=int)
        parser.add_argument("-mn","--minutes", help="Lookback window in minutes, default 0", default=0,type=int)
        try:
            args = parser.parse_args(shlex.split(args))
            if any(value < 0 for value in (args.minutes, args.hours, args.days)):
                parser.error("Lookback windows must not be negative.")
            timetotal_minutes = args.minutes + (args.hours * 60) + (args.days * 1440)
            if timetotal_minutes == 0:
                timetotal_minutes = 1440  # default to last 24 hours
            time_reference = datetime.now(timezone.utc) - timedelta(minutes=timetotal_minutes)
            time_reference_z = time_reference.isoformat(timespec="seconds").replace("+00:00", "Z")
            filters = [f"created>={time_reference_z}"]
            if args.dataset:
                filters.append(f"referenced_datasets=={args.dataset}")
            if args.state:
                filters.append(f"state=={args.state}")
            aepp_query = queryservice.QueryService(config=self.config)
            queries = aepp_query.getQueries(property=",".join(filters), orderby="-created")
            list_queries = [
                {
                    "id": q.get("id","N/A"),
                    "created": q.get("created"),
                    "client": q.get("client","N/A"),
                    "elapsedTime": q.get("elapsedTime","N/A"),
                    "userId": q.get("userId","N/A"),
                }
                for q in queries
                if q.get("client") in ("Adobe Query Service UI", "Generic PostgreSQL")
            ]
            df_queries = pd.DataFrame(list_queries, columns=["id", "created", "client", "elapsedTime", "userId"])
            df_queries.to_csv(f"{self.config.sandbox}_queries.csv",index=False)
            table = Table(title=f"Queries in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="cyan")
            table.add_column("Created", style="yellow")
            table.add_column("Client", style="white")
            table.add_column("Elapsed Time (ms)", style="white")
            for q in list_queries[:10]:
                table.add_row(
                    q.get("id","N/A"),
                    str(q.get("created") or "N/A"),
                    q.get("client","N/A"),
                    str(q.get("elapsedTime","N/A"))
                )
            console.print(table)
            console.print(f"Queries exported to {self.config.sandbox}_queries.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_query(self,args:Any)->None:
        """Display query metadata, SQL and execution state by query ID."""
        parser = argparse.ArgumentParser(prog='get_query', add_help=True)
        parser.add_argument("query_id", help="ID of the query to retrieve", type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_query = queryservice.QueryService(config=self.config)
            result:dict = aepp_query.getQuery(queryId=args.query_id)
            if not result.get("id"):
                raise ValueError(f"Query retrieval failed: {result}")
            console.print_json(data=result)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return


    @login_required
    def do_get_query_templates(self,args:Any) -> None:
        """List all query templates in the current sandbox with ID, name and creation date."""
        parser = argparse.ArgumentParser(prog='get_query_templates', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_query = queryservice.QueryService(config=self.config)
            templates:list = aepp_query.getTemplates(n_results="inf")
            table = Table(title=f"Queries templates in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="yellow")
            table.add_column("Created", style="white")
            for t in templates:
                table.add_row(
                    str(t.get("id", "N/A")),
                    str(t.get("name", "N/A")),
                    str(t.get("created") or "N/A").split('.')[0]
                )
            console.print(table)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_query_template(self,args:Any) -> None:
        """Display a query template by ID and export query_template_<id>.json."""
        parser = argparse.ArgumentParser(prog='get_query_template', add_help=True)
        parser.add_argument("template_id", help="ID of the query template to retrieve", type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_query = queryservice.QueryService(config=self.config)
            result:dict = aepp_query.getTemplate(templateId=args.template_id)
            if not result.get("id"):
                raise ValueError(f"Query template retrieval failed: {result}")
            console.print_json(data=result)
            with open(f'query_template_{args.template_id}.json', 'w') as f:
                json.dump(result, f, indent=4)
            console.print(f"Query template saved to query_template_{args.template_id}.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_queries_scheduled(self,args:Any) -> None:
        """List all query schedules and export queries_scheduled_<sandbox>.json."""
        parser = argparse.ArgumentParser(prog='get_queries_scheduled', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_query = queryservice.QueryService(config=self.config)
            results:list = aepp_query.getSchedules(n_results="inf")
            table = Table(title=f"Queries Scheduled in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="yellow")
            table.add_column("Start Date", style="blue")
            table.add_column("Schedule", style="white")
            table.add_column("Enabled", style="white")
            for result in results:
                schedule_state = result.get("state", "N/A")
                if schedule_state == "ENABLED":
                    state = "[green]True[/green]"
                elif schedule_state == "DISABLED":
                    state = "[red]False[/red]"
                else:
                    state = f"[yellow]{schedule_state}[/yellow]"
                table.add_row(
                    str(result.get("id", "")),
                    str(result.get("query",{}).get("name") or ""),
                    str(result.get('schedule',{}).get("startDate") or ""),
                    str(result.get('schedule',{}).get("schedule") or ""),
                    state
                )
            console.print(table)
            with open(f'queries_scheduled_{self.config.sandbox}.json', 'w') as f:
                json.dump(results, f, indent=4)
            console.print(f"Queries scheduled saved to queries_scheduled_{self.config.sandbox}.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_create_query_scheduled(self,args:Any)->None:
        """
        Schedule SQL (-q) or a template (-t) in the current sandbox.
        Requires -sch/--schedule and -sd/--start_date; accepts optional -a key=value,key=value,
        -n/--name, -d/--description and -ed/--end_date. Dates must include a timezone.
        Adobe automatically enables the schedule after registration.
        """
        parser = argparse.ArgumentParser(prog='create_query_scheduled')
        parser.add_argument("-n",'--name', help="Name of the query", type=str)
        parser.add_argument("-d", "--description", help="Description of the query", type=str)
        source = parser.add_mutually_exclusive_group(required=True)
        source.add_argument("-q", "--query", help="SQL query to be scheduled (e.g. 'SELECT * FROM table')", type=str)
        source.add_argument("-t", "--template_id", help="Template ID for the query", type=str)
        parser.add_argument("-a", "--arguments", help="SQL/template parameters: key1=value1,key2=value2", type=str)
        parser.add_argument("-sch", "--schedule", help="Cron expression (at most hourly) or shorthand such as @daily or @once", required=True, type=str)
        parser.add_argument("-sd", "--start_date", help="ISO 8601 start date with timezone (e.g. '2026-11-01T00:00:00Z')", required=True, type=str)
        parser.add_argument("-ed", "--end_date", help="Optional ISO 8601 end date with timezone, later than start date", type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            if not (args.query or args.template_id) or not args.schedule.strip():
                parser.error("SQL/template ID and schedule must not be empty.")
            schedule = {"schedule": args.schedule}
            dates:dict[str, datetime] = {}
            for key, value in (("startDate", args.start_date), ("endDate", args.end_date)):
                if value is None:
                    continue
                try:
                    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    parser.error(f"{key} must be an ISO 8601 timestamp with timezone.")
                if date.tzinfo is None:
                    parser.error(f"{key} must include a timezone, such as Z or +02:00.")
                dates[key] = date
                timespec = "milliseconds" if date.microsecond % 1000 == 0 else "microseconds"
                schedule[key] = date.astimezone(timezone.utc).isoformat(timespec=timespec).replace("+00:00", "Z")
            if "endDate" in dates and dates["endDate"] <= dates["startDate"]:
                parser.error("End date must be later than start date.")
            query:dict[str, Any] = {"dbName": f"{self.config.sandbox}:all"}
            if args.template_id:
                query["templateId"] = args.template_id
            else:
                query["sql"] = args.query
            if args.name is not None:
                query["name"] = args.name
            if args.description is not None:
                query["description"] = args.description
            if args.arguments is not None:
                arguments = {}
                for item in args.arguments.split(","):
                    key, separator, value = item.partition("=")
                    if not separator or not key.strip():
                        parser.error("Arguments must be comma-separated key=value pairs with non-empty keys.")
                    arguments[key.strip()] = value
                query["queryParameters"] = arguments
            aepp_query = queryservice.QueryService(config=self.config)
            res = aepp_query.createSchedule(scheduleQuery={"query": query, "schedule": schedule})
            if not res.get("id"):
                raise ValueError(f"Schedule creation failed: {res}")
            console.print_json(data=res)
            console.print(f"Schedule creation accepted (ID: {res['id']}, state: {res.get('state', 'N/A')}). Adobe enables it after registration.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_enable_query_scheduled(self,args:Any)->None:
        """Request enabling a registered query schedule by ID; the change is asynchronous."""
        parser = argparse.ArgumentParser(prog='enable_query_scheduled', add_help=True)
        parser.add_argument("schedule_id", help="ID of the scheduled query to enable", type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_query = queryservice.QueryService(config=self.config)
            res = aepp_query.enableSchedule(scheduleId=args.schedule_id)
            if res.get("statusCode") != 202:
                raise ValueError(f"Schedule enable request failed: {res}")
            console.print(f"Enable request accepted for scheduled query {args.schedule_id}.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_disable_query_scheduled(self,args:Any)->None:
        """Request disabling a registered query schedule by ID; the change is asynchronous."""
        parser = argparse.ArgumentParser(prog='disable_query_scheduled', add_help=True)
        parser.add_argument("schedule_id", help="ID of the scheduled query to disable", type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_query = queryservice.QueryService(config=self.config)
            res = aepp_query.disableSchedule(scheduleId=args.schedule_id)
            if res.get("statusCode") != 202:
                raise ValueError(f"Schedule disable request failed: {res}")
            console.print(f"Disable request accepted for scheduled query {args.schedule_id}.", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_query(self,args:Any) -> None:
        """Execute a SQL query against the current sandbox, save the result to a CSV file and display a sample."""
        parser = argparse.ArgumentParser(prog='query', add_help=True)
        parser.add_argument("sql_query", help="SQL query to execute",type=str)
        parser.add_argument("-fn", help="if you want to save it to a specific filename",type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_query = queryservice.QueryService(config=self.config)
            conn = aepp_query.connection()
            iqs2 = queryservice.InteractiveQuery2(conn)
            result:pd.DataFrame = iqs2.query(sql=args.sql_query)
            if args.fn:
                if args.fn.endswith('.csv'):
                    filename=args.fn
                else:
                    filename=f"{args.fn}.csv"
            else:
                filename=f"query_result_{int(datetime.now().timestamp())}.csv"
            result.to_csv(filename, index=False)
            if len(result) < 10: ## no need to sample if less than 10 rows
                sample = result.head()
            else:
                sample = result.sample(5)
            iqs2.close() ## stopping the connection
            console.print(sample)
            console.print(f"Query result exported to {filename}", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
        
    @login_required
    def do_query_audience_population(self,args:Any) -> None:
        """Retrieve the segment identities for a specific segment, save the result to a CSV file."""
        parser = argparse.ArgumentParser(prog='query_audience_population', add_help=True)
        parser.add_argument("audience_id", help="Audience ID(s) to query population for",type=str,nargs='+')
        parser.add_argument("-ef", "--extra_fields", help="Extra fields to include in the query, comma-separated",type=str,nargs='?')
        parser.add_argument("-c","--count_only", help="if you want to get only the count of the segment population",action='store_true',default=False)
        parser.add_argument("-fn","--filename", help="if you want to save it to a specific filename",type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            if args.filename:
                filename = args.filename if args.filename.endswith('.csv') else f"{args.filename}.csv"
            else:
                filename = f"audience_population_{args.audience_id[0]}.csv"
            aepp_query = queryservice.QueryService(config=self.config)
            conn = aepp_query.connection()
            iqs2 = queryservice.InteractiveQuery2(conn, config=self.config)
            result:pd.DataFrame = iqs2.queryAudiencePopulation(audienceId=args.audience_id, extraFields=args.extra_fields,count=args.count_only)
            result.to_csv(filename, index=False)
            console.print(f"Audience population exported to {filename}", style="green")
            iqs2.close()
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_query_history_meta(self, arg: str) -> None:
        """Retrieve a table's snapshot history metadata, display a sample and export it to CSV."""
        parser = argparse.ArgumentParser(prog="query_history_meta")
        parser.add_argument("table", help="Query Service table name")
        parser.add_argument("-fn", "--filename", help="Output CSV filename")
        try:
            args = parser.parse_args(shlex.split(arg))
            aepp_query = queryservice.QueryService(config=self.config)
            conn = aepp_query.connection()
            iqs2 = queryservice.InteractiveQuery2(conn, config=self.config)
            try:
                result: pd.DataFrame = iqs2.queryHistoryMeta(table=args.table)
            finally:
                iqs2.close()
            filename = args.filename or f"{self.config.sandbox}_history_meta.csv"
            if not filename.endswith(".csv"):
                filename = f"{filename}.csv"
            result.to_csv(filename, index=False)
            if result.empty:
                console.print("No rows returned.", style="yellow")
            else:
                console.print(result.head(10))
            console.print(f"Query result exported to {filename}", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    def _display_profile_trend(
        self,
        result: pd.DataFrame,
        series_columns: tuple[str, ...] = (),
        metric: str = "COUNT_OF_PROFILES",
    ) -> None:
        missing = {"DATE_KEY", *series_columns}.difference(result.columns)
        if missing:
            raise ValueError(f"Cannot plot trend: missing columns {', '.join(sorted(missing))}")
        data = result.copy()
        numeric_columns: dict[str, pd.Series] = {}
        for column in data.columns:
            if column in {"DATE_KEY", *series_columns} or pd.api.types.is_bool_dtype(data[column]):
                continue
            values = pd.to_numeric(data[column], errors="coerce")
            if values.notna().any() and not (data[column].notna() & values.isna()).any():
                numeric_columns[column] = values
        metric_column = next((column for column in numeric_columns if column.casefold() == metric.casefold()), None)
        if metric_column is None:
            available = ", ".join(numeric_columns) or "(none)"
            raise ValueError(f"Cannot plot metric {metric!r}. Available metrics: {available}")
        values = numeric_columns[metric_column]
        if values.isna().any() or not values.map(isfinite).all():
            raise ValueError(f"Cannot plot trend: {metric_column} must contain finite numeric values")
        data[metric_column] = values
        dates = data["DATE_KEY"].astype(str).str.replace(r"^(\d{4})(\d{2})(\d{2})$", r"\1-\2-\3", regex=True)
        data["DATE_KEY"] = pd.to_datetime(dates, errors="raise")
        if data["DATE_KEY"].isna().any():
            raise ValueError("Cannot plot trend: DATE_KEY must contain valid dates")
        data = data.sort_values("DATE_KEY", kind="stable")

        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt

        figure, axes = plt.subplots(figsize=(10, 5))
        try:
            groups = data.groupby(list(series_columns), sort=False, dropna=False) if series_columns else [(metric_column, data)]
            for key, series in groups:
                labels = key if isinstance(key, tuple) else (key,)
                label = " / ".join("Unknown" if pd.isna(value) else str(value) for value in labels)
                axes.plot(series["DATE_KEY"], series[metric_column], marker="o", markersize=4, label=label)
            locator = mdates.AutoDateLocator(minticks=3, maxticks=8)
            axes.xaxis.set_major_locator(locator)
            axes.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
            axes.set_xlabel("Date")
            axes.set_ylabel(metric_column)
            axes.set_title(f"{metric_column} trend")
            axes.ticklabel_format(axis="y", style="plain", useOffset=False)
            axes.grid(True, alpha=0.3)
            if series_columns:
                axes.legend()
            figure.autofmt_xdate()
            figure.tight_layout()
            plt.show(block=True)
        finally:
            plt.close(figure)

    def _display_namespace_distribution(self, result: pd.DataFrame) -> None:
        missing = {"NAMESPACE_DESCRIPTION", "COUNT_OF_PROFILES"}.difference(result.columns)
        if missing:
            raise ValueError(f"Cannot plot distribution: missing columns {', '.join(sorted(missing))}")
        data = result.copy()
        counts = pd.to_numeric(data["COUNT_OF_PROFILES"], errors="raise")
        if counts.isna().any() or not counts.map(isfinite).all() or (counts < 0).any():
            raise ValueError("Cannot plot distribution: profile counts must be finite, non-negative numbers")
        data["COUNT_OF_PROFILES"] = counts
        data = data.sort_values("COUNT_OF_PROFILES", ascending=False, kind="stable")
        maximum = float(data["COUNT_OF_PROFILES"].max()) or 1
        width = max(1, min(30, console.width // 3))
        ascii_only = False
        try:
            "\u2588\u2589\u258a\u258b\u258c\u258d\u258e\u258f".encode(console.encoding)
        except UnicodeEncodeError:
            ascii_only = True
        table = Table(
            title="Namespace profile distribution",
            caption="Bars are relative to the largest namespace count, not percentages",
            box=box.ASCII if ascii_only else box.SQUARE,
        )
        table.add_column("Namespace", overflow="fold")
        table.add_column("Profiles", justify="right")
        table.add_column("Distribution")
        for namespace, count in zip(data["NAMESPACE_DESCRIPTION"], data["COUNT_OF_PROFILES"]):
            label = "Unknown" if pd.isna(namespace) else str(namespace)
            bar = Text("#" * round(count / maximum * width), style="cyan") if ascii_only else Bar(
                size=maximum, begin=0, end=float(count), width=width, color="cyan",
            )
            table.add_row(Text(label), f"{count:,.0f}", bar)
        console.print(table)

    @login_required
    def do_query_profiles_trend(self, arg: str) -> None:
        """Retrieve profile trends, optionally plot a metric against dates, and export them to CSV."""
        parser = argparse.ArgumentParser(prog="query_profiles_trend")
        parser.add_argument("-fn", "--filename", help="Output CSV filename")
        parser.add_argument("--plot", action="store_true", help="Open a Matplotlib trend chart with dates on the X axis")
        parser.add_argument("--metric", help="Numeric result column for the Y axis (default: COUNT_OF_PROFILES; requires --plot)")
        try:
            args = parser.parse_args(shlex.split(arg))
            if args.metric is not None and not args.plot:
                parser.error("--metric requires --plot")
            aepp_query = queryservice.QueryService(config=self.config)
            conn = aepp_query.connection()
            iqs2 = queryservice.InteractiveQuery2(conn, config=self.config)
            try:
                result: pd.DataFrame = iqs2.queryProfilesTrend()
            finally:
                iqs2.close()
            filename = args.filename or f"{self.config.sandbox}_profiles_trend.csv"
            if not filename.endswith(".csv"):
                filename = f"{filename}.csv"
            result.to_csv(filename, index=False)
            if result.empty:
                console.print("No rows returned.", style="yellow")
            else:
                console.print(result.head(10))
            console.print(f"Query result exported to {filename}", style="green")
            if args.plot and not result.empty:
                metric = "COUNT_OF_PROFILES" if args.metric is None else args.metric
                self._display_profile_trend(result, metric=metric)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_query_namespaces_distribution(self, arg: str) -> None:
        """Retrieve the latest namespace distribution, optionally show a bar chart, and export it to CSV."""
        parser = argparse.ArgumentParser(prog="query_namespaces_distribution")
        parser.add_argument("-fn", "--filename", help="Output CSV filename")
        parser.add_argument("--plot", action="store_true", help="Display a Rich bar chart of namespace profile counts")
        try:
            args = parser.parse_args(shlex.split(arg))
            aepp_query = queryservice.QueryService(config=self.config)
            conn = aepp_query.connection()
            iqs2 = queryservice.InteractiveQuery2(conn, config=self.config)
            try:
                result: pd.DataFrame = iqs2.queryNamespacesDistribution()
            finally:
                iqs2.close()
            filename = args.filename or f"{self.config.sandbox}_namespaces_distribution.csv"
            if not filename.endswith(".csv"):
                filename = f"{filename}.csv"
            result.to_csv(filename, index=False)
            if result.empty:
                console.print("No rows returned.", style="yellow")
            else:
                console.print(result.head(10))
            console.print(f"Query result exported to {filename}", style="green")
            if args.plot and not result.empty:
                self._display_namespace_distribution(result)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_query_namespaces_trend(self, arg: str) -> None:
        """Retrieve namespace trends, optionally filter or plot a metric against dates, and export them to CSV."""
        parser = argparse.ArgumentParser(prog="query_namespaces_trend")
        parser.add_argument("-ns", "--namespace", help="Namespace name to filter by (case-insensitive)")
        parser.add_argument("-fn", "--filename", help="Output CSV filename")
        parser.add_argument("--plot", action="store_true", help="Open a Matplotlib trend chart with one line per namespace")
        parser.add_argument("--metric", help="Numeric result column for the Y axis (default: COUNT_OF_PROFILES; requires --plot)")
        try:
            args = parser.parse_args(shlex.split(arg))
            if args.metric is not None and not args.plot:
                parser.error("--metric requires --plot")
            aepp_query = queryservice.QueryService(config=self.config)
            conn = aepp_query.connection()
            iqs2 = queryservice.InteractiveQuery2(conn, config=self.config)
            try:
                result: pd.DataFrame = iqs2.queryNamespacesTrend(namespace=args.namespace)
            finally:
                iqs2.close()
            filename = args.filename or f"{self.config.sandbox}_namespaces_trend.csv"
            if not filename.endswith(".csv"):
                filename = f"{filename}.csv"
            result.to_csv(filename, index=False)
            if result.empty:
                console.print("No rows returned.", style="yellow")
            else:
                console.print(result.head(10))
            console.print(f"Query result exported to {filename}", style="green")
            if args.plot and not result.empty:
                metric = "COUNT_OF_PROFILES" if args.metric is None else args.metric
                self._display_profile_trend(result, series_columns=("NAMESPACE",), metric=metric)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_query_audience_population_trend(self, arg: str) -> None:
        """Retrieve audience population trends, optionally filter or plot a metric against dates, and export them to CSV."""
        parser = argparse.ArgumentParser(prog="query_audience_population_trend")
        parser.add_argument("-a", "--audience", help="Segment name or audience ID to filter by (case-insensitive)")
        parser.add_argument("-fn", "--filename", help="Output CSV filename")
        parser.add_argument("--plot", action="store_true", help="Open a Matplotlib trend chart with one line per audience")
        parser.add_argument("--metric", help="Numeric result column for the Y axis (default: COUNT_OF_PROFILES; requires --plot)")
        try:
            args = parser.parse_args(shlex.split(arg))
            if args.metric is not None and not args.plot:
                parser.error("--metric requires --plot")
            aepp_query = queryservice.QueryService(config=self.config)
            conn = aepp_query.connection()
            iqs2 = queryservice.InteractiveQuery2(conn, config=self.config)
            try:
                result: pd.DataFrame = iqs2.queryAudiencePopulationTrend(segment=args.audience)
            finally:
                iqs2.close()
            filename = args.filename or f"{self.config.sandbox}_audience_population_trend.csv"
            if not filename.endswith(".csv"):
                filename = f"{filename}.csv"
            result.to_csv(filename, index=False)
            if result.empty:
                console.print("No rows returned.", style="yellow")
            else:
                console.print(result.head(10))
            console.print(f"Query result exported to {filename}", style="green")
            if args.plot and not result.empty:
                metric = "COUNT_OF_PROFILES" if args.metric is None else args.metric
                self._display_profile_trend(result, series_columns=("AUDIENCE_NAME", "AUDIENCE_ID"), metric=metric)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_profile_attributes(self,args:Any) -> None:
        """Use Profile API to get the UPS Profile storage attributes for a specific user, saving it in a JSON file"""
        parser = argparse.ArgumentParser(prog='get_profile_attributes', add_help=True)
        parser.add_argument("-uid","--user_id", help="User ID of the user", default=None,type=str)
        parser.add_argument("-ns","--namespace", help="Namespace of the user", default=None,type=str)
        parser.add_argument("-m","--merge_policy",help="Merge policy ID to apply when retrieving attributes", type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_profile = customerprofile.Profile(config=self.config)
            attributes = aepp_profile.getEntity(entityId=args.user_id,entityIdNS=args.namespace,mergePolicyId=args.merge_policy)
            with open(f"{self.config.sandbox}_{args.user_id}_profile_attributes.json", 'w') as f:
                json.dump(attributes, f, indent=4)
            dataXDM = attributes[list(attributes.keys())[0]].get("entity")
            if 'segmentMembership' in dataXDM:
                del dataXDM['segmentMembership']
            console.print_json(data=dataXDM)
            console.print(f"Profile attributes exported to {self.config.sandbox}_{args.user_id}_profile_attributes.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_profile_events(self,args:Any) -> None:
        """Retrieve all UPS events for a specific user, saving it in a JSON file"""
        parser = argparse.ArgumentParser(prog='get_profile_events', add_help=True)
        parser.add_argument("-uid","--user_id", help="User ID of the user", default=None,type=str)
        parser.add_argument("-ns","--namespace", help="Namespace of the user", default=None,type=str)
        parser.add_argument("-m","--merge_policy",help="Merge policy ID to apply when retrieving attributes", type=str)
        parser.add_argument("-l","--limit",help="Max Amount of events that is being returned. Default 1000, max 5000", type=int,default=1000)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_profile = customerprofile.Profile(config=self.config)
            events = aepp_profile.getEntityEvents(entityId=args.user_id,entityIdNS=args.namespace,mergePolicyId=args.merge_policy,n_events=args.limit)
            with open(f"{self.config.sandbox}_{args.user_id}_profile_events.json", 'w') as f:
                json.dump(events, f, indent=4)
            summary_data = {
                "eventTypes":{},
                "primaryIdentities":{},
                "totalEvents":0,
                "firstEventTimestamp":"",
                "lastEventTimestamp":"",
            }
            for ev in events:
                summary_data["totalEvents"] += 1
                eventType = ev.get("entity",{}).get("eventType","unknown")
                if eventType not in summary_data["eventTypes"]:
                    summary_data["eventTypes"][eventType] = 1
                else:
                    summary_data["eventTypes"][eventType] += 1
                timestamp = ev.get("entity",{}).get("timestamp","")
                if summary_data["firstEventTimestamp"] == "" or timestamp < summary_data["firstEventTimestamp"]:
                    summary_data["firstEventTimestamp"] = timestamp
                if summary_data["lastEventTimestamp"] == "" or timestamp > summary_data["lastEventTimestamp"]:
                    summary_data["lastEventTimestamp"] = timestamp
                primaryIdentity = ev.get("primaryIdentity",{}).get("namespaceCode","")
                if primaryIdentity not in summary_data["primaryIdentities"].keys():
                    summary_data["primaryIdentities"][primaryIdentity] = 1
                else:
                    summary_data["primaryIdentities"][primaryIdentity] += 1
            console.print_json(data=summary_data)
            console.print(f"Profile attributes exported to {self.config.sandbox}_{args.user_id}_profile_event_attributes.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_get_account_attributes(self,args:Any) -> None:
        """Get the account attributes defined in the current sandbox based on the b2b_account by default, saving it in a JSON file"""
        parser = argparse.ArgumentParser(prog='get_account_attributes', add_help=True)
        parser.add_argument("-uid","--user_id", help="User ID of the user", default=None,type=str)
        parser.add_argument("-ns","--namespace", help="Namespace of the user", default="b2b_account",type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_profile = customerprofile.Profile(config=self.config)
            account_attributes = aepp_profile.getEntity(
                entityId=args.user_id,
                entityIdNS=args.namespace,
                schema_name='_xdm.context.account'
            )
            with open(f"{self.config.sandbox}_account_attributes.json", 'w') as f:
                json.dump(account_attributes, f, indent=4)
            console.print_json(data=account_attributes)
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
        
    @login_required
    def do_get_merge_policies(self,args:Any) -> None:
        """Get the list of merge policies defined in the current sandbox, saving it in a JSON file"""
        parser = argparse.ArgumentParser(prog='get_merge_policies', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_profile = customerprofile.Profile(config=self.config)
            merge_policies = aepp_profile.getMergePolicies()
            with open(f"{self.config.sandbox}_merge_policies.json", 'w') as f:
                json.dump(merge_policies, f, indent=4)
            table = Table(title=f"Merge Policies in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="yellow")
            table.add_column("Schema", style="white")
            table.add_column("Type", style="white")
            table.add_column("Active On Edge", style="green")
            table.add_column("Default", style="magenta")
            for q in merge_policies:
                table.add_row(
                    q.get("id","N/A"),
                    q.get("name","N/A"),
                    q.get("schema",{}).get("name","N/A"),
                    q.get("attributeMerge",{}).get("type","N/A"),
                    str(q.get("isActiveOnEdge",False)),
                    str(q.get("default",False)),
                )
            console.print(table)
            console.print(f"Merge policies exported to {self.config.sandbox}_merge_policies.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
        
    @login_required
    def do_get_hygiene_works(self,args:Any) -> None:
        """Get the work orders from Data Hygiene API, saving them in a JSON file and optionally filtering by work order ID"""
        parser = argparse.ArgumentParser(prog="get_hygiene_works",description="Get the work orders from Data Hygiene")
        parser.add_argument('-f','--filter',help="filter the work orders by the work order ID that contains that string", type=str)
        parser.add_argument('-d','--days', help='Timeframe in days to filter work orders by creation date, default 0 (no filter)', default=0, type=int)
        try:
            args = parser.parse_args(shlex.split(args))
            from aepp import hygiene
            hygiene_client = hygiene.Hygiene(config=self.config)
            works = hygiene_client.getWorkOrders()
            if args.filter:
                works = [work for work in works if args.filter in work.get("workorderId", "")]
            if args.days > 0:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=args.days)
                works = [work for work in works if datetime.fromisoformat(work.get("createdAt", "1970-01-01T00:00:00+00:00")) >= cutoff_date]
            with open(f"{self.config.sandbox}_hygiene_works.json", 'w') as f:
                json.dump(works, f, indent=4)
            console.print_json(data=works)
            console.print(f"Hygiene work orders exported to {self.config.sandbox}_hygiene_works.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_hygiene_work(self,args:Any) -> None:
        """Get the work status from Data Hygiene API, saving them in a JSON file and optionally filtering by work order ID"""
        parser = argparse.ArgumentParser(prog="get_hygiene_work",description="Get the work status from Data Hygiene")
        parser.add_argument('workOrderId',help="The unique ID of the work order to retrieve", type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            from aepp import hygiene
            hygiene_client = hygiene.Hygiene(config=self.config)
            if not args.workOrderId:
                console.print("Please provide a work order ID using the 'workOrderId' argument", style="red")
                return
            work = hygiene_client.getWorkOrderStatus(args.workOrderId)
            with open(f"{self.config.sandbox}_hygiene_work_{args.workOrderId}.json", 'w') as f:
                json.dump(work, f, indent=4)
            console.print_json(data=work)
            console.print(f"Hygiene work order exported to {self.config.sandbox}_hygiene_work_{args.workOrderId}.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_hygiene_quotas(self,args:Any) -> None:
        """Get the current quota and usage for Data Hygiene API, saving them in a JSON file"""
        parser = argparse.ArgumentParser(prog="get_hygiene_quotas",description="Get the current quota and usage for Data Hygiene API", add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            from aepp import hygiene
            hygiene_client = hygiene.Hygiene(config=self.config)
            quotas = hygiene_client.getQuotas()
            if type(quotas) == list and len(quotas) == 1:
                quotas = quotas[0]
            with open(f"{self.config.sandbox}_hygiene_quotas.json", 'w') as f:
                json.dump(quotas, f, indent=4)
            console.print_json(data=quotas)
            console.print(f"Hygiene quotas exported to {self.config.sandbox}_hygiene_quotas.json", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return

    @login_required
    def do_extract_artifacts(self,args:Any) -> None:
        """extract all artifacts from the current sandbox to a localfolder"""
        parser = argparse.ArgumentParser(prog='extract_artifacts', description='Extract artifacts from AEP to a local folder',add_help=True)
        parser.add_argument('-lf','--localfolder', help='Local folder to extract artifacts to', default='./extractions')
        parser.add_argument('-f','--filters', help='Name to be used to filter schemas and datasets extraction. It does not impact other artifact types. Multiple filters can be separated by space.', nargs='*', default=None)
        parser.add_argument('-at','--artifact_types', help="The type of artifact to extract. Possible values are: 'class','schema','fieldgroup','datatype','descriptor','dataset','identity','mergepolicy','audience'. If not provided, it will extract all the artifacts", nargs='*', default=None)
        parser.add_argument('-v','--verbose', help='Enable verbose output, optionally passing True or False (default False)', nargs='?', const=True, default=False, type=str2bool)
        try:
            console.print("Extracting artifacts...", style="blue")
            args = parser.parse_args(shlex.split(args))
            aepp.extractSandboxArtifacts(
                sandbox=self.config,
                localFolder=args.localfolder,
                filters=args.filters,
                artifactTypes=args.artifact_types,
                verbose=args.verbose
            )
            console.print(Panel("Extraction completed!", style="green"))
        except SystemExit:
            return
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")

    @login_required
    def do_extract_artifact(self,args:Any) -> None:
        """extract_artifact from the current sandbox to a localfolder"""
        parser = argparse.ArgumentParser(prog='extract_artifact', description='Extract a specific artifact from AEP to a local folder',add_help=True)
        parser.add_argument('artifact', help='artifact to extract (name or id): "schema","fieldgroup","datatype","descriptor","dataset","identity","mergepolicy","audience"')
        parser.add_argument('-at','--artifactType', help='artifact type ')
        parser.add_argument('-lf','--localfolder', help='Local folder to extract artifacts to',default='extractions')
        parser.add_argument('-v','--verbose', help='Enable verbose output, optionally passing True or False (default False)', nargs='?', const=True, default=False, type=str2bool)
        try:
            console.print("Extracting artifact...", style="blue")
            args = parser.parse_args(shlex.split(args))
            aepp.extractSandboxArtifact(
                artifact=args.artifact,
                artifactType=args.artifactType,
                sandbox=self.config,
                localFolder=args.localfolder,
                verbose=args.verbose
            )
            console.print("Extraction completed!", style="green")
        except SystemExit:
            return
        except Exception as e:
            if str(e) == "list index out of range":
                console.print(f"(!) Error: Artifact [blue]'{args.artifact}'[/blue] of type [blue]'{args.artifactType}'[/blue] not found in sandbox '{self.config.sandbox}'", style="red")
            else:        
                console.print(f"(!) Error: {str(e)}", style="red")

    @login_required
    def do_sync(self,args:Any) -> None:
        """sync all artifacts based on the parameters provided (local folder or base sandbox) to a target sandbox(s)"""
        parser = argparse.ArgumentParser(prog='sync', description='Synchronizing artifacts to an AEP Sandbox, either from sandbox or from local storage',add_help=True)
        parser.add_argument('artifact', help='artifact to sync (name or id)')
        parser.add_argument('-at','--artifactType', help='artifact type that has been passed, these type are supported: "schema","fieldgroup","datatype","descriptor","dataset","identity","mergepolicy","audience" ',type=str)
        parser.add_argument('-t','--targets', help='target sandboxes',nargs='+',type=str)
        parser.add_argument('-lf','--localfolder', help='Local folder(s) to use for sync (if not using base sandbox)',default=None,nargs='+',type=str)
        parser.add_argument('-b','--baseSandbox', help='Base sandbox for synchronization (if not using local folder)',type=str)
        parser.add_argument('-v','--verbose', help='Enable verbose output (default True)',default=True,type=str2bool)
        parser.add_argument("-f","--force",help="Boolean. force the creation or synchronization of the artefact. (Default False)",default=False,type=str2bool)
        try:
            args = parser.parse_args(shlex.split(args))
            console.print("Initializing Synchronizor...", style="blue")
            if args.baseSandbox:
                synchronizor = synchronizer.Synchronizer(
                    config=self.config,
                    targets=args.targets,
                    baseSandbox=args.baseSandbox,
                )
            elif args.localfolder:
                synchronizor = synchronizer.Synchronizer(
                    config=self.config,
                    targets=args.targets,
                    localFolder=args.localfolder,
            )
            else:
                synchronizor = synchronizer.Synchronizer(
                    config=self.config,
                    targets=args.targets,
                    baseSandbox=self.config.sandbox,
                )
            console.print("Starting Sync...", style="blue")
            synchronizor.syncComponent(
                component=args.artifact,
                componentType=args.artifactType,
                verbose=args.verbose,
                force=args.force
            )
            console.print("Sync completed!", style="green")
        except SystemExit:
            return
        except Exception as e:
            if str(e) == "list index out of range":
                console.print(f"(!) Error: Artifact [blue]'{args.artifact}'[/blue] of type [blue]'{args.artifactType}'[/blue] not found", style="red")
            else:
                console.print(f"(!) Error: {str(e)}", style="red")
    
    @login_required
    def do_sync_all(self,args:Any) -> None:
        """sync all artifacts based on the parameters provided (ONLY local folder) to a target sandbox(s)"""
        parser = argparse.ArgumentParser(prog='sync_all', description='Synchronizing all artifacts to an AEP Sandbox, either from sandbox or from local storage',add_help=True)
        parser.add_argument('-t','--targets', help='target sandboxes',nargs='+',type=str)
        parser.add_argument('-lf','--localfolder', help='Local folder(s) to use for sync',default='extractions',nargs='+',type=str)
        parser.add_argument('-v','--verbose', help='Enable verbose output (default True)',default=True,type=str2bool)
        parser.add_argument("-f","--force", help="Boolean. force the creation or synchronization of the artefact. (Default False)",default=False,type=str2bool)
        try:
            args = parser.parse_args(shlex.split(args))
            console.print("Initializing Synchronizor...", style="blue")
            synchronizor = synchronizer.Synchronizer(
                config=self.config,
                targets=args.targets,
                localFolder=args.localfolder)
            console.print("Starting Sync...", style="blue")
            synchronizor.syncAll(verbose=args.verbose,force=args.force)
            console.print("Sync completed!", style="green")
        except SystemExit:
            return
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")

    @login_required
    def do_build_graph(self,args:Any) -> None:
        """Build a graph of all artifacts in the current sandbox and save it as a JSON file"""
        parser = argparse.ArgumentParser(prog='build_graph', description='Build a graph of all artifacts in the current sandbox',add_help=True)
        parser.add_argument('-hd','--has_data', help='Boolean. If you want to retrieved information for all schemas and datasets. Default True', type=str2bool,default=True)
        parser.add_argument('-d','--detail', help='Boolean. If you want to retrieved the path information for the schema and fieldgroups. Default True', type=str2bool, default=True)
        parser.add_argument('-e','--enabled', help='Boolean. If you want to build the knowledge graph based on enabled dataset only. Default False', type=str2bool,default=False)
        parser.add_argument('-ex','--export', help='Boolean. If you want to export the graph to a turtle file. Default False', type=str2bool,default=False)
        parser.add_argument('-v','--verbose', help='Boolean. If you want to see the progress of the graph building. Default True', type=str2bool,default=False)
        try:
            args = parser.parse_args(shlex.split(args))
            console.print(f"Building knowledge graph for {self.sandbox}", style="blue")
            kn = knowledgegraph.KnowledgeGraph(config=self.config)
            self.graph = kn.buildGraph(hasdata=args.has_data,detail=args.detail, enabled=args.enabled,verbose=args.verbose)
            if args.export:
                kn.exportTurtle(graph=self.graph, path=f"{self.config.sandbox}.ttl")
                console.print(f"Knowledge graph built and exported to {self.config.sandbox}.ttl", style="green")
            else:
                console.print(Panel("Graph build completed!", style="green"))
        except SystemExit:
            return
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")

    @login_required
    def do_export_graph(self,args:Any) -> None:
        """Export the previously built graph to a turtle file"""
        parser = argparse.ArgumentParser(prog='export_graph', description='Export the previously built graph to a turtle file',add_help=True)
        parser.add_argument('filename', help='Filename to export the graph to (e.g., graph.ttl)', type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            if self.graph is None:
                console.print("No graph has been built yet. Please run 'build_graph' first.", style="red")
                return
            kn = knowledgegraph.KnowledgeGraph(config=self.config)
            kn.exportTurtle(graph=self.graph, path=args.filename)
            console.print(f"Knowledge graph exported to {args.filename}", style="green")
        except SystemExit:
            return
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        
    @login_required
    def do_load_graph(self,args:Any) -> None:
        """Load a graph from a turtle file"""
        parser = argparse.ArgumentParser(prog='load_graph', description='Load a graph from a turtle file',add_help=True)
        parser.add_argument('filename', help='Filename to load the graph from (e.g., graph.ttl)', type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            kn = knowledgegraph.KnowledgeGraph(config=self.config)
            self.graph = kn.loadGraph(path=args.filename)
            console.print(f"Knowledge graph loaded from {args.filename}", style="green")
        except SystemExit:
            return
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
    
    @login_required
    def do_add_path_attributes(self,args:Any) -> None:
        """Add path attributes to the previously built graph. Attributes are passed as --attributes predicate1=value1 predicate2=value2 ..."""
        parser = argparse.ArgumentParser(prog='add_path_attributes', description='Add path attributes to the previously built graph',add_help=True)
        parser.add_argument('-p','--path', type=str, help='path to add the attributes to', required=True)
        parser.add_argument('-a','--attributes', nargs='+', help='Attributes to add in the form predicate=value', required=True, action=ParseDict)    
        try:
            args = parser.parse_args(shlex.split(args))
            if self.graph is None:
                console.print("No graph has been built yet. Please run 'build_graph' first.", style="red")
                return
            kn = knowledgegraph.KnowledgeGraph(config=self.config)
            if self.graph is None:
                console.print("No graph has been built yet. Please run 'build_graph' first.", style="red")
                return
            else:
                kn.loadGraph(graph=self.graph)
            self.graph = kn.addPathAttributes(path=args.path, attributes=args.attributes)
            console.print("Path attributes added to the graph.", style="green")
        except SystemExit:
            return
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")

    @login_required
    def do_add_schema_attributes(self,args:Any) -> None:
        """Add schema attributes to the previously built graph. Attributes are passed as --attributes predicate1=value1 predicate2=value2 ..."""
        parser = argparse.ArgumentParser(prog='add_schema_attributes', description='Add schema attributes to the previously built graph',add_help=True)
        parser.add_argument('-s','--schema', type=str, help='schema $id to add the attributes to', required=True)
        parser.add_argument('-a','--attributes', nargs='+', help='Attributes to add in the form predicate=value', required=True, action=ParseDict)    
        try:
            args = parser.parse_args(shlex.split(args))
            if self.graph is None:
                console.print("No graph has been built yet. Please run 'build_graph' first.", style="red")
                return
            kn = knowledgegraph.KnowledgeGraph(config=self.config)
            if self.graph is None:
                console.print("No graph has been built yet. Please run 'build_graph' first.", style="red")
                return
            else:
                kn.loadGraph(graph=self.graph)
            self.graph = kn.addSchemaAttributes(schema=args.schema, attributes=args.attributes)
            console.print("Schema attributes added to the graph.", style="green")
        except SystemExit:
            return
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        
    @login_required
    def do_add_dataset_attributes(self,args:Any) -> None:
        """Add dataset attributes to the previously built graph. Attributes are passed as --attributes predicate1=value1 predicate2=value2 ..."""
        parser = argparse.ArgumentParser(prog='add_dataset_attributes', description='Add dataset attributes to the previously built graph',add_help=True)
        parser.add_argument('-d','--dataset', type=str, help='dataset ID to add the attributes to', required=True)
        parser.add_argument('-a','--attributes', nargs='+', help='Attributes to add in the form predicate=value', required=True, action=ParseDict)    
        try:
            args = parser.parse_args(shlex.split(args))
            if self.graph is None:
                console.print("No graph has been built yet. Please run 'build_graph' first.", style="red")
                return
            kn = knowledgegraph.KnowledgeGraph(config=self.config)
            if self.graph is None:
                console.print("No graph has been built yet. Please run 'build_graph' first.", style="red")
                return
            else:
                kn.loadGraph(graph=self.graph)
            self.graph = kn.addDatasetAttributes(dataset=args.dataset, attributes=args.attributes)
            console.print("Dataset attributes added to the graph.", style="green")
        except SystemExit:
            return
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")

    COMMAND_GROUPS = {
        "System": ["config", 
                   "create_config_file", 
                   "get_sandboxes", 
                   "change_sandbox",
                   "create_sandbox",
                   "get_tags"],
        "Schema": ["get_schemas",
                   "get_classes",
                   "get_ups_schemas",
                   "get_ups_fieldgroups",
                   "get_ups_fieldgroups",
                   "get_profile_schemas",
                   "get_event_schemas",
                   "get_union_profile_json",
                   "get_union_profile_csv",
                   "get_union_event_json",
                   "get_union_event_csv",
                   "get_schema_xdm",
                   "get_schema_csv",
                   "get_schema_json",
                   "get_fieldgroups",
                   "get_fieldgroup_json",
                   "get_fieldgroup_csv",
                   "get_fieldgroup_xdm",
                   "delete_fieldgroup",
                   "get_datatypes",
                   "get_datatype_json",
                   "get_datatype_csv",
                   "get_datatype_xdm",
                   "enable_schema_for_ups",
                   "create_fieldgroup_template",
                   "upload_fieldgroup_definition_csv",
                   "upload_fieldgroup_definition_xlsx",
                   "upload_fieldgroup_definition_xdm",
                   "create_b2b_artifacts",
                   "get_descriptors",
                   "get_descriptor"
                   ],
        "Datasets": ["get_datasets",
                     "get_dataset",
                     "get_datasets_tablenames",
                     "get_datasets_infos",
                     "get_observable_schema_json",
                     "get_observable_schema_csv",
                     "get_snapshot_datasets",
                     "get_dataset_expiration",
                     "set_dataset_expiration",
                     "createDataset",
                     "enable_dataset",
                     "enable_dataset_for_ups",
                     "enable_dataset_for_uis",
                     "get_tags",],
        "Audiences":["get_audiences","create_audiences_job",
                     "flexible_audience_evaluation",
                     "get_batch_evaluation",
                     "update_batch_evaluation_time",
                     "extract_audience_paths",
                     "extract_audience_ref"],
        "Flows": ["get_flows",
                  "get_flow_errors",
                  "get_flow_partial_success",
                  "create_dataset_http_source",
                  "get_DLZ_credential"],
        "Deletion": ["delete_dataset",
                     "delete_schema",
                     "delete_dataflow",
                     "delete_audience"],
        "Queries": ["get_queries",
                    "get_query",
                    "get_query_templates",
                    "get_query_template",
                    "get_queries_scheduled",
                    "create_query_scheduled",
                    "enable_query_scheduled",
                    "disable_query_scheduled",
                    "query",
                    "query_audience_population",
                    "query_history_meta",
                    "query_profiles_trend",
                    "query_namespaces_distribution",
                    "query_namespaces_trend",
                    "query_audience_population_trend"],
        "Hygiene": ["get_hygiene_works","get_hygiene_work","get_hygiene_quotas"],
        "Profiles": [
                    "get_identities",
                    "create_identity",
                    "get_merge_policies",
                    "get_profile_attributes",
                    "get_account_attributes",
                     "get_profile_events",
                     "get_profile_attributes_lineage",
                     "get_profile_attribute_lineage",
                     "get_event_attributes_lineage",
                     "get_event_attribute_lineage"],
        "Synchronization": ["extract_artifacts",
                            "extract_artifact",
                            "sync",
                            "sync_all"],
        "Knowledge Graph": ["build_graph",
                            "export_graph",
                            "load_graph",
                            "add_path_attributes",
                            "add_dataset_attributes",
                            "add_schema_attributes"],
        "Misc": ["help", "exit", "EOF"]

    }
    
    def do_help(self, arg):
        if arg:
            # If user asks for specific help (e.g., 'help sync'), use default behavior
            super().do_help(arg)
        else:
            # Custom grouped layout for the main help screen
            print("\nDocumented commands (type help <topic>):")
            print("==========================================")
            for group, commands in self.get_grouped_commands().items():
                print(f"\n{group}:")
                print("-" * (len(group) + 1))
                # Format the list of commands into a clean string
                for command in commands:
                    print("  " + command)
            print()
            print()
    
    def do_clear(self, arg:Any) -> None:
        """Clear the terminal screen."""
        clear_terminal()

    def get_grouped_commands(self):
        # This maps the defined groups to actual commands available in the class
        all_cmds = [n[3:] for n in self.get_names() if n.startswith('do_')]
        grouped = {group: [] for group in self.COMMAND_GROUPS}
        grouped["Misc"] = []

        for c in all_cmds:
            found = False
            for group, cmds in self.COMMAND_GROUPS.items():
                if c in cmds:
                    grouped[group].append(c)
                    found = True
                    break
            if not found and c != 'help': # Hide help from its own list
                grouped["Misc"].append(c)
        return grouped
    
    def do_exit(self, args:Any) -> None:
        """Exit the application"""
        console.print(Panel("Exiting...", style="blue"))
        return True  # Stops the loop

    def do_EOF(self, args:Any) -> None:
        """Handle Ctrl+D"""
        console.print(Panel("Exiting...", style="blue"))
        return True

# --- 3. The Entry Point ---#

def main():
    # ARGPARSE: Handles the initial setup flags
    parser = argparse.ArgumentParser(description="Interactive Client Tool",add_help=True)

    # Optional: Allow passing user/pass via flags to skip the interactive login step
    parser.add_argument("-sx", "--sandbox", help="Auto-login sandbox")
    parser.add_argument("-s", "--secret", help="Secret")
    parser.add_argument("-o", "--org_id", help="Auto-login org ID")
    parser.add_argument("-sc", "--scopes", help="Scopes")
    parser.add_argument("-cid", "--client_id", help="Auto-login client ID")
    parser.add_argument("-cf", "--config_file", help="Path to config file", default=None)
    parser.add_argument("-cmd", "--command", help="Run a single command non-interactively and exit (e.g. 'get_schemas -f client')", default=None)
    parser.add_argument("-v", "--version", action="version", version=f"aepp {aepp.__version__}")
    args = parser.parse_args()
    cmd_arg = args.command
    shell_kwargs = {k: v for k, v in vars(args).items() if k != "command"}
    shell = ServiceShell(**shell_kwargs)
    if cmd_arg is not None:
        shell.onecmd(cmd_arg)
        return
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        console.print(Panel("\nForce closing...", style="red"))

if __name__ == "__main__":
    main()