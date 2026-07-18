#!/usr/bin/env python3
#
# Copyright (c) Contributors to the Open 3D Engine Project.
# For complete copyright and license terms please see the LICENSE at the root of this distribution.
#
# SPDX-License-Identifier: Apache-2.0 OR MIT
#
"""Collect and verify a local, redacted Developer Preview 0 diagnostics bundle.

The command does not launch FoA, upload data, read saves, deploy files, or include
source artifact contents. Review every generated file before sharing it.
"""
from __future__ import annotations
import sys
from pathlib import Path
TOOLS_DIR=Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path: sys.path.insert(0,str(TOOLS_DIR))
from developer_preview_diagnostics_support import *
def collect_bundle(*,output_dir,repo_root,build_dir,project_root,workspace_root,validation_result,launch_result,editor_logs,maximum_log_bytes,replace,argv,runner=default_command_runner):
    output_dir=output_dir.resolve(strict=False)
    for root,label in ((workspace_root,"workspace"),(project_root,"project")):
        if root is not None and (output_dir==root or is_relative_to(output_dir,root)): raise DiagnosticsError(f"Diagnostics output must not be inside the explicit {label} root.")
    prepare_output_directory(output_dir,replace); replacements=known_path_replacements(repo_root=repo_root,build_dir=build_dir,project_root=project_root,workspace_root=workspace_root); generated_at=utc_now()
    tools=redact_value(collect_tool_summary(repo_root,runner),replacements=replacements); system="Developer Preview 0 diagnostics - local system summary\n\n"+"".join(f"[{name}] exit_code={value['exit_code']}\n{value['output']}\n\n" for name,value in sorted(tools.items())); system=redact_text(system,replacements=replacements); assert_redacted_text(system,SYSTEM_NAME); atomic_write(output_dir/SYSTEM_NAME,system.encode())
    build=redact_value({"schema_version":SCHEMA_VERSION,"build_directory":str(build_dir or ""),"configuration":parse_cmake_cache(build_dir) if build_dir else {"status":"not-supplied"}},replacements=replacements); atomic_write(output_dir/BUILD_NAME,canonical_json_bytes(build)); optional=[]
    for source,name,label in ((validation_result,VALIDATION_NAME,"validation result"),(launch_result,LAUNCH_NAME,"launch result")):
        if source is not None: atomic_write(output_dir/name,canonical_json_bytes(redact_value(load_json_result(source,label),replacements=replacements))); optional.append(name)
    if workspace_root is not None: atomic_write(output_dir/INVENTORY_NAME,canonical_json_bytes(workspace_inventory(workspace_root))); optional.append(INVENTORY_NAME)
    logs=[]
    for index,path in enumerate(editor_logs,start=1):
        excerpt=redact_text(read_log_excerpt(path,maximum_log_bytes),replacements=replacements); assert_redacted_text(excerpt,str(path)); safe=re.sub(r"[^A-Za-z0-9._-]+","-",path.name).strip("-") or "Editor.log"; relative=f"logs/{index:02d}-{safe}.log"; atomic_write(output_dir/relative,excerpt.encode()); logs.append(relative)
    summary={"schema_version":SCHEMA_VERSION,"bundle_id":BUNDLE_ID,"generated_at_utc":generated_at,"command":"developer_preview_diagnostics.py collect","arguments":redact_value(list(argv),replacements=replacements,key="arguments"),"files":[SYSTEM_NAME,BUILD_NAME,*optional,*logs],"source_artifact_contents_included":False,"uploaded":False,"review_required_before_sharing":True}; atomic_write(output_dir/SUMMARY_NAME,canonical_json_bytes(summary))
    readme="Developer Preview 0 diagnostics bundle\n======================================\n\nThis directory was generated locally and was not uploaded. Review every file before sharing it. Review every generated file before sharing it.\nThe collector excludes source artifact contents, game files, saves, credentials, environment variables, and unrestricted filesystem listings. Paths and secret-like values are redacted.\n\nRun the verify command before sharing. Delete any file you do not want to disclose.\n"; atomic_write(output_dir/README_NAME,readme.encode())
    manifest=build_manifest(output_dir,generated_at); atomic_write(output_dir/MANIFEST_NAME,canonical_json_bytes(manifest)); verify_bundle(output_dir); return manifest
def infer_editor_logs(project_root,explicit_logs):
    if explicit_logs: return list(explicit_logs)
    if project_root is None: return []
    return [path for path in (project_root/"user/log/Editor.log",project_root/"user/log/Editor.log.1") if path.is_file()]
def build_parser():
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest="command",required=True)
    collect=sub.add_parser("collect",help="Collect a redacted local diagnostics directory."); collect.add_argument("--output",type=Path,required=True); collect.add_argument("--repo-root",type=Path); collect.add_argument("--build-dir",type=Path); collect.add_argument("--project",type=Path); collect.add_argument("--workspace-root",type=Path); collect.add_argument("--validation-result",type=Path); collect.add_argument("--launch-result",type=Path); collect.add_argument("--editor-log",type=Path,action="append",default=[]); collect.add_argument("--max-log-bytes",type=int,default=MAX_LOG_BYTES_DEFAULT); collect.add_argument("--replace",action="store_true")
    verify=sub.add_parser("verify",help="Verify hashes, allow-list, size limits, and redaction."); verify.add_argument("--output",type=Path,required=True); return parser
def main(argv=None):
    arguments=list(argv if argv is not None else sys.argv[1:]); args=build_parser().parse_args(arguments)
    try:
        if args.command=="verify":
            output=resolve_path(args.output,Path.cwd()); verify_bundle(output); print(f"Developer Preview 0 diagnostics bundle verified: {output}"); return 0
        repo=resolve_path(args.repo_root or repository_root_from_script(),Path.cwd()); output=resolve_path(args.output,Path.cwd()); build=resolve_path(args.build_dir,repo) if args.build_dir else None; project=resolve_path(args.project,repo) if args.project else None; workspace=resolve_path(args.workspace_root,repo) if args.workspace_root else None; validation=resolve_path(args.validation_result,repo) if args.validation_result else None; launch=resolve_path(args.launch_result,repo) if args.launch_result else None; explicit=[resolve_path(path,repo) for path in args.editor_log]
        collect_bundle(output_dir=output,repo_root=repo,build_dir=build,project_root=project,workspace_root=workspace,validation_result=validation,launch_result=launch,editor_logs=infer_editor_logs(project,explicit),maximum_log_bytes=args.max_log_bytes,replace=args.replace,argv=arguments); print(f"Developer Preview 0 diagnostics collected: {output}"); print("Review every generated file before sharing. Nothing was uploaded."); return 0
    except (DiagnosticsError,OSError,ValueError) as exc: print(f"Developer Preview 0 diagnostics failed: {exc}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
