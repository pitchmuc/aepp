from html import parser
from matplotlib.pyplot import table
import aepp
from aepp import synchronizer, schema, schemamanager, fieldgroupmanager, datatypemanager, identity, queryservice,catalog,flowservice,sandboxes, segmentation, customerprofile
from aepp.cli.upsfieldsanalyzer import UpsFieldsAnalyzer
import argparse, cmd, shlex, json
from functools import wraps
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from pathlib import Path
from io import FileIO
import pandas as pd
from datetime import datetime
import urllib.parse
from typing import Any, Concatenate, ParamSpec, ParamSpecKwargs
from collections.abc import Callable

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

console = Console()

# --- 2. The Interactive Shell ---
class ServiceShell(cmd.Cmd):
    def __init__(self, **kwargs:ParamSpecKwargs) -> None:
        super().__init__()
        self.config = None
        self.connectInstance = True
        self.ups_profile_analyzer:UpsFieldsAnalyzer|None = None
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

    def do_change_sandbox(self, args:Any) -> None:
        """Change the current sandbox after configuration"""
        parser = argparse.ArgumentParser(prog='change sandbox', add_help=True)
        parser.add_argument("sandbox", help="sandbox name to switch to",type=str)
        try:
            args = parser.parse_args(shlex.split(args))
            if args.sandbox is None:
                 console.print(Panel("(!) Please provide a sandbox name using -sx or --sandbox", style="red"))
                 return
            config_sandbox = sandboxes.Sandboxes(config=self.config)
            list_sandboxes = config_sandbox.getSandboxes()
            if args.sandbox not in [sb.get("name") for sb in list_sandboxes]:
                console.print(Panel(f"(!) Sandbox '{args.sandbox}' not found in your org. Please provide a valid sandbox name.", style="red"))
                return
            if self.config is not None:
                if args.sandbox:
                    self.config.setSandbox(str(args.sandbox))
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
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            schemas = aepp_schema.getSchemas()
            if len(schemas) > 0:
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
    def do_get_ups_schemas(self, args) -> None:
        """List all schemas enabled for Profile in the current sandbox. By default do not save the output to a file as it can be very long, use the --save option to export the data to a CSV file."""
        parser = argparse.ArgumentParser(prog='get_schemas_enabled', add_help=True)
        parser.add_argument("-sv", "--save",help="Boolean. Save enabled schemas to CSV file. Default False. Possible values: True, False",type=bool,default=False)
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
        parser.add_argument("-sv", "--save",help="Boolean. Save enabled field groups to CSV file. Default False. Possible values: True, False",type=bool,default=False)
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
    def do_get_profile_schemas(self,args:Any) -> None:
        """Get the current schema based on Profile class. By default do not save the output to a file as it can be very long, use the --save option to export the data to a CSV file."""
        parser = argparse.ArgumentParser(prog='get_schemas_enabled', add_help=True)
        parser.add_argument("-sv", "--save",help="Boolean. Save profile schemas to CSV file. Default False. Possible values: True, False",type=bool,default=False)
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
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full schema information with all details. Default False. Possible values: True, False",type=bool)
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
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full schema information with all details. Default False. Possible values: True, False",type=bool)
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
        parser.add_argument("-sv", "--save",help="Boolean. Save event schemas to CSV file. Default False. Possible values: True, False",type=bool,default=False)
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
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full schema with all details. Default False. Possible values: True, False",type=bool)
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
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full schema information with all details. Default False. Possible values: True, False",type=bool)
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
        parser.add_argument("-sv", "--save",help="Boolean. Save field groups to CSV file. Default False. Possible values: True, False",type=bool,default=False)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            fieldgroups = aepp_schema.getFieldGroups()
            if args.save and fieldgroups:
                df_fgs = pd.DataFrame(fieldgroups)
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
            ## chech if schema title is found
            if args.fieldgroup in [fg for fg in aepp_schema.data.fieldGroups_altId.keys()]:
                my_fieldgroup_manager = fieldgroupmanager.FieldGroupManager(
                    fieldgroup=aepp_schema.data.fieldGroups_altId[args.fieldgroup],
                    config=self.config
                )
            else:
                my_fieldgroup_manager = fieldgroupmanager.FieldGroupManager(
                    fieldgroup=args.fieldgroup,
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
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full field group information with all details. Default False. Possible values: True, False",type=bool)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            fieldgroups = aepp_schema.getFieldGroups()
            ## chech if schema title is found
            if args.fieldgroup in [fg for fg in aepp_schema.data.fieldGroups_altId.keys()]:
                my_fieldgroup_manager = fieldgroupmanager.FieldGroupManager(
                    fieldgroup=aepp_schema.data.fieldGroups_altId[args.fieldgroup],
                    config=self.config
                )
            else:
                my_fieldgroup_manager = fieldgroupmanager.FieldGroupManager(
                    fieldgroup=args.fieldgroup,
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
        parser.add_argument("-f","--full",default=False,help="Boolean. Get full data type information with all details. Default False. Possible values: True, False",type=bool)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_schema = schema.Schema(config=self.config)
            datatypes = aepp_schema.getDataTypes()
            ## chech if schema title is found
            if args.datatype in [dt for dt in aepp_schema.data.dataTypes_altId.keys()]:
                my_datatype_manager = datatypemanager.DataTypeManager(
                    datatype=aepp_schema.data.dataTypes_altId[args.datatype],
                    config=self.config
                )
            else:
                my_datatype_manager = datatypemanager.DataTypeManager(
                    datatype=args.datatype,
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
                    datatype=aepp_schema.data.dataTypes_altId[args.datatype],
                    config=self.config
                )
            else:
                my_datatype_manager = datatypemanager.DataTypeManager(
                    datatype=args.datatype,
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
        parser.add_argument("-ts","--test",help="Boolean. Test creation without uploading it to AEP. It will output a JSON file. Default False. Possible values: True, False",default=False,type=bool)
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
    def do_upload_fieldgroup_definition_xdm(self,args:Any) -> None:
        """Upload a field group definition from a JSON XDM file"""
        parser = argparse.ArgumentParser(prog='upload_fieldgroup_definition_xdm', add_help=True)
        parser.add_argument("xdm_path", help="Path to the field group JSON XDM file")
        parser.add_argument("-ts","--test",help="Boolean. Test upload without uploading it to AEP. It will output a JSON file. Default False. Possible values: True, False",default=False,type=bool)
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
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
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
    def do_get_datasets_tablenames(self, args:Any) -> None:
        """List all datasets with their table names in the current sandbox"""
        parser = argparse.ArgumentParser(prog='get_datasets_tablenames', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getDataSets(output='list')
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
            myObs = catalog.ObservableSchemaManager(schema_json,config=self.config)
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
            myObs = catalog.ObservableSchemaManager(schema_json,config=self.config)
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
    def do_get_snapshot_datasets(self,args:Any) -> None:
        """List all snapshot datasets in the current sandbox"""
        parser = argparse.ArgumentParser(prog='get_snapshot_datasets', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_cat = catalog.Catalog(config=self.config)
            datasets = aepp_cat.getProfileSnapshotDatasets(explicitMergePolicy=True)
            list_ds = []
            for key, ds in datasets.items():
                obj = ds
                obj['id'] = key
                list_ds.append(obj)
            df_datasets = pd.DataFrame(list_ds)
            df_datasets.to_csv(f"{self.config.sandbox}_snapshot_datasets.csv",index=False)
            table = Table(title=f"Snapshot Datasets in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="white")
            table.add_column("Table Name", style="white")
            table.add_column("Merge Policy Name", style="yellow")
            table.add_column("Merge Policy ID", style="green")
            for ds in list_ds:
                table.add_row(
                    ds.get("id","N/A"),
                    ds.get("tags",{}).get('adobe/pqs/table',["N/A"])[0],
                    ds.get('mergePolicyName','N/A'),
                    [el.split(':')[1] for el in ds.get('tags',{}).get('unifiedProfile',[]) if el.startswith('mergePolicyId')][0]
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
        parser.add_argument("-co","--custom_only",help="Get only custom identities", default=False,type=bool)
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
        """List all audiences in the current sandbox"""
        parser = argparse.ArgumentParser(prog='get_audiences', add_help=True)
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_audience = segmentation.Segmentation(config=self.config)
            audiences = aepp_audience.getAudiences()
            flw = flowservice.FlowService(config=self.config)
            destinations = flw.getFlows(onlyDestinations=True)
            segments_shared = []
            for tmpFlow in destinations:
                if len(tmpFlow['transformations'])>0:
                    tmpSegmentShared = tmpFlow['transformations'][0].get('params',{}).get('segmentSelectors',{}).get('selectors',[])
                    for s in tmpSegmentShared:
                        s['flowId'] = tmpFlow['id']
                    segments_shared += tmpSegmentShared
            segment_shared_dict = {seg.get('value',{}).get('id'):{
                "exportMode" : seg.get('value',{}).get('exportMode'),
                "scheduleFrequency": seg.get('value',{}).get("schedule",{}).get('frequency',''),
                "flowId" : seg["flowId"]
            } for seg in segments_shared}
            for aud in audiences:
                aud['usedInFlow'] = True if segment_shared_dict.get(aud.get("id","N/A"),{}) != {} else False
                aud['sharedInfo'] = segment_shared_dict.get(aud.get("id","N/A"),{})    
            df_audiences = pd.DataFrame(audiences)
            df_audiences.to_csv(f"{self.config.sandbox}_audiences.csv",index=False)   
            table = Table(title=f"Audiences in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Evaluation", style="yellow")
            table.add_column("Total Profiles", style="green")
            table.add_column("In Flow", style="white")
            for aud in audiences:
                table.add_row(
                    aud.get("id","N/A"),
                    aud.get("name","N/A"),
                    '[bright_blue]Batch[/bright_blue]' if aud.get("evaluationInfo",{}).get("batch",{}).get('enabled') else '[chartreuse1]Streaming[/chartreuse1]' if aud.get("evaluationInfo",{}).get("continuous",{}).get('enabled') else '[purple]Edge[/purple]' if aud.get("evaluationInfo",{}).get("synchronous",{}).get('enabled') else 'N/A',
                    str(aud.get('metrics',{}).get('data',{}).get('totalProfiles','N/A')),
                    '[green3]True[/green3]' if aud.get("usedInFlow",False) else '[red3]False[/red3]',
                )
            console.print(table)
            console.print(f"Audiences exported to {self.config.sandbox}_audiences.csv", style="green")
        except Exception as e:
            console.print(f"(!) Error: {str(e)}", style="red")
        except SystemExit:
            return
    
    @login_required
    def do_get_tags(self,args)->None:
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
        """List flows in the current sandbox based on parameters provided. By default, list all sources and destinations."""
        parser = argparse.ArgumentParser(prog='get_flows', add_help=True)
        parser.add_argument("-i","--internal_flows",help="Boolean. Get internal flows. Default False. Possible values: True, False", default=False,type=bool)
        parser.add_argument("-adv","--advanced",help="Boolean. Get advanced information about runs. Default False. Possible values: True, False", default=False,type=bool)
        parser.add_argument("-ao","--active_only",help="Boolean. Get only active flows during that time period. Default True. Possible values: True, False", default=True,type=bool)
        parser.add_argument("-mn","--minutes", help="Timeframe in minutes to check for errors, default 0", default=0,type=int)
        parser.add_argument("-H","--hours", help="Timeframe in hours to check for errors, default 0", default=0,type=int)
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
            if args.internal_flows:
                list_flows = flows
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
        parser.add_argument("-H","--hours", help="Timeframe in hours to check for errors, default 0", default=0,type=int)
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
    def do_get_queries(self, args:Any)-> None:
        """List top 1000 queries in the current sandbox for the last 24 hours by default, optionally filtered by dataset ID. Display top 10 in console and export all to a CSV file."""
        parser = argparse.ArgumentParser(prog='get_queries', add_help=True)
        parser.add_argument("-ds","--dataset", help="Dataset ID to filter queries", default=None)
        parser.add_argument("-st","--state", help="State to filter queries (running, completed, failed)", default=None)
        parser.add_argument("-H","--hours", help="Timeframe in hours to check for errors, default 0", default=0,type=int)
        parser.add_argument("-d","--days", help="Timeframe in days to check for errors, default 0", default=0,type=int)
        parser.add_argument("-mn","--minutes", help="Timeframe in minutes to check for errors, default 0", default=0,type=int)  
        try:
            args = parser.parse_args(shlex.split(args))
            timetotal_minutes = args.minutes + (args.hours * 60) + (args.days * 1440)
            if timetotal_minutes == 0:
                timetotal_minutes = 1440  # default to last 24 hours
            time_reference = int(datetime.now().timestamp()) - (timetotal_minutes * 60)
            time_reference_z = datetime.fromtimestamp(time_reference).isoformat() + 'Z'
            params = {'property':f'created>={time_reference_z}','orderBy':'-created'}
            if args.dataset:
                if params['property'] == '':
                    params['property'] = f'referenced_datasets=={args.dataset}'
                else:
                    params['property'] += f',referenced_datasets=={args.dataset}'
            if params['property'] == '':
                params = None
            else:
                params['property'] = urllib.parse.quote(params['property'])
            aepp_query = queryservice.QueryService(config=self.config)
            queries = aepp_query.getQueries(property=params['property'] if params else None, orderby=params['orderBy'])
            list_queries = []
            for q in queries:
                if q['client'] == "Adobe Query Service UI" or q["client"] == 'Generic PostgreSQL':
                    list_queries.append(q) 
            for q in list_queries:
                obj = {
                    "id": q.get("id","N/A"),
                    "created": q.get("created"),
                    "client": q.get("client","N/A"),
                    "elapsedTime": q.get("elapsedTime","N/A"),
                    "userId": q.get("userId","N/A"),
                }
                list_queries.append(obj)
            df_queries = pd.DataFrame(list_queries)
            df_queries.to_csv(f"{self.config.sandbox}_queries.csv",index=False)
            table = Table(title=f"Queries in Sandbox: {self.config.sandbox}")
            table.add_column("ID", style="cyan")
            table.add_column("Created", style="yellow")
            table.add_column("Client", style="white")
            table.add_column("Elapsed Time (ms)", style="white")
            for q in list_queries[:10]:
                table.add_row(
                    q.get("id","N/A"),
                    q.get("created","N/A"),
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
            sample = result.sample(5)
            console.print(sample)
            console.print(f"Query result exported to {filename}", style="green")
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
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_profile = customerprofile.Profile(config=self.config)
            attributes = aepp_profile.getEntity(entityId=args.user_id,entityIdNS=args.namespace)
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
        try:
            args = parser.parse_args(shlex.split(args))
            aepp_profile = customerprofile.Profile(config=self.config)
            events = aepp_profile.getEntityEvents(entityId=args.user_id,entityIdNS=args.namespace)
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
    def do_extract_artifacts(self,args:Any) -> None:
        """extract all artifacts from the current sandbox to a localfolder"""
        parser = argparse.ArgumentParser(prog='extract_artifacts', description='Extract artifacts from AEP to a local folder',add_help=True)
        parser.add_argument('-lf','--localfolder', help='Local folder to extract artifacts to', default='./extractions')
        parser.add_argument('-rg','--region', help='Region to extract artifacts from: "ndl2" (default), "va7", "aus5", "can2", "ind2"',default='ndl2')
        try:
            console.print("Extracting artifacts...", style="blue")
            args = parser.parse_args(shlex.split(args))
            aepp.extractSandboxArtifacts(
                sandbox=self.config,
                localFolder=args.localfolder,
                region=args.region
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
        parser.add_argument('-rg','--region', help='Region to extract artifacts from: "ndl2" (default), "va7", "aus5", "can2", "ind2"',default='ndl2')
        try:
            console.print("Extracting artifact...", style="blue")
            args = parser.parse_args(shlex.split(args))
            aepp.extractSandboxArtifact(
                artifact=args.artifact,
                artifactType=args.artifactType,
                sandbox=self.config,
                localFolder=args.localfolder
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
        parser.add_argument('-lf','--localfolder', help='Local folder(s) to use for sync',default='extractions',nargs='+',type=str)
        parser.add_argument('-b','--baseSandbox', help='Base sandbox for synchronization (if not using local folder)',type=str)
        parser.add_argument('-v','--verbose', help='Enable verbose output (default True)',default=True,type=bool)
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
            console.print("Starting Sync...", style="blue")
            synchronizor.syncComponent(
                component=args.artifact,
                componentType=args.artifactType,
                verbose=args.verbose
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
        """sync all artifacts based on the parameters provided (local folder or base sandbox) to a target sandbox(s)"""
        parser = argparse.ArgumentParser(prog='sync_all', description='Synchronizing all artifacts to an AEP Sandbox, either from sandbox or from local storage',add_help=True)
        parser.add_argument('-t','--targets', help='target sandboxes',nargs='+',type=str)
        parser.add_argument('-lf','--localfolder', help='Local folder(s) to use for sync',default='extractions',nargs='+',type=str)
        parser.add_argument('-b','--baseSandbox', help='Base sandbox for synchronization (if not using local folder)',type=str)
        parser.add_argument('-v','--verbose', help='Enable verbose output (default True)',default=True,type=bool)
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
            console.print("Starting Sync...", style="blue")
            synchronizor.syncAll(verbose=args.verbose)
            console.print("Sync completed!", style="green")
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
                    "get_datatypes",
                    "get_datatype_json",
                    "get_datatype_csv",
                    "enable_schema_for_ups",
                    "create_fieldgroup_template",
                    "upload_fieldgroup_definition_csv",
                    "upload_fieldgroup_definition_xdm"
                   ],
        "Datasets": ["get_datasets",
                     "get_datasets_tablenames",
                     "get_datasets_infos",
                     "get_observable_schema_json",
                     "get_observable_schema_csv",
                     "get_snapshot_datasets",
                     "createDataset",
                     "enable_dataset",
                     "enable_dataset_for_ups",
                     "enable_dataset_for_uis",
                     "get_tags",],
        "Audiences":["get_audiences"],
        "Flows": ["get_flows",
                  "get_flow_errors",
                  "create_dataset_http_source",
                  "get_DLZ_credential"],
        "Queries": ["get_queries",
                    "query"],
        "Profiles": [
                    "get_identities",
                    "create_identity",
                    "get_profile_attributes",
                     "get_profile_events",
                     "get_profile_attributes_lineage",
                     "get_profile_attribute_lineage",
                     "get_event_attributes_lineage",
                     "get_event_attribute_lineage"],
        "Synchronization": ["extract_artifacts",
                            "extract_artifact",
                            "sync",
                            "sync_all"],
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
    args = parser.parse_args() 
    shell = ServiceShell(**vars(args))
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        console.print(Panel("\nForce closing...", style="red"))

if __name__ == "__main__":
    main()