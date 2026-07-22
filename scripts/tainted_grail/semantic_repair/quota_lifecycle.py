"""Release records and deterministic compaction for repeated-compaction quota ledgers."""
from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from typing import Any,Iterable
from .compaction_quota import CompactionQuotaLedger,CompactionQuotaReservation
from .errors import CheckpointProofError
_ZERO_HASH="0"*64
def _canonical(doc:dict[str,Any])->bytes:return (json.dumps(doc,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode()
def _sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
@dataclass(frozen=True)
class CompactionQuotaReleaseRecord:
 release_index:int;source_ledger_sha256:str;operation_id:str;operation_index:int;released_backup_bytes:int;operation_sha256:str;previous_release_sha256:str;reason:str
 def __post_init__(self):
  if type(self.release_index)is not int or self.release_index<=0:raise CheckpointProofError("quota release index must be positive")
  if not isinstance(self.operation_id,str)or not self.operation_id.strip():raise CheckpointProofError("quota release operation_id must be non-empty")
  if type(self.operation_index)is not int or self.operation_index<=0:raise CheckpointProofError("quota release operation index must be positive")
  if type(self.released_backup_bytes)is not int or self.released_backup_bytes<0:raise CheckpointProofError("quota released bytes are invalid")
  if any(not isinstance(v,str)or len(v)!=64 for v in(self.source_ledger_sha256,self.operation_sha256,self.previous_release_sha256)):raise CheckpointProofError("quota release hash is invalid")
  if not isinstance(self.reason,str)or not self.reason.strip():raise CheckpointProofError("quota release reason must be non-empty")
 def to_dict(self):return {"schema_version":1,"authority":"synthetic-compaction-quota-release-only","runtime_authority":"none","promotion":"none","effect":"quota-reservation-released-metadata-only","release_index":self.release_index,"source_ledger_sha256":self.source_ledger_sha256,"operation_id":self.operation_id,"operation_index":self.operation_index,"released_backup_bytes":self.released_backup_bytes,"operation_sha256":self.operation_sha256,"previous_release_sha256":self.previous_release_sha256,"reason":self.reason}
 def to_bytes(self):return _canonical(self.to_dict())
 @property
 def sha256(self):return _sha(self.to_bytes())
 @classmethod
 def from_bytes(cls,data):
  try:doc=json.loads(data.decode())
  except Exception as exc:raise CheckpointProofError("invalid quota release record")from exc
  expected={"schema_version","authority","runtime_authority","promotion","effect","release_index","source_ledger_sha256","operation_id","operation_index","released_backup_bytes","operation_sha256","previous_release_sha256","reason"}
  if not isinstance(doc,dict)or set(doc)!=expected or doc["schema_version"]!=1 or doc["authority"]!="synthetic-compaction-quota-release-only" or doc["runtime_authority"]!="none" or doc["promotion"]!="none" or doc["effect"]!="quota-reservation-released-metadata-only":raise CheckpointProofError("quota release record boundary is invalid")
  return cls(doc["release_index"],doc["source_ledger_sha256"],doc["operation_id"],doc["operation_index"],doc["released_backup_bytes"],doc["operation_sha256"],doc["previous_release_sha256"],doc["reason"])
@dataclass(frozen=True)
class CompactionQuotaLedgerCompactionRecord:
 source_ledger_sha256:str;release_record_sha256s:tuple[str,...];released_operation_ids:tuple[str,...];released_backup_bytes:int;remaining_operation_ids:tuple[str,...];remaining_backup_bytes:int;compacted_ledger_sha256:str
 def __post_init__(self):
  if any(not isinstance(v,str)or len(v)!=64 for v in(self.release_record_sha256s+(self.source_ledger_sha256,self.compacted_ledger_sha256)):raise CheckpointProofError("quota compaction hash is invalid")
  if self.released_operation_ids!=tuple(sorted(self.released_operation_ids))or self.remaining_operation_ids!=tuple(sorted(self.remaining_operation_ids)):raise CheckpointProofError("quota operation IDs must be sorted")
  if set(self.released_operation_ids)&set(self.remaining_operation_ids):raise CheckpointProofError("released and remaining operations overlap")
 def to_dict(self):return {"schema_version":1,"authority":"synthetic-compaction-quota-ledger-compaction-only","runtime_authority":"none","promotion":"none","effect":"ledger-compacted-provenance-retained","source_ledger_sha256":self.source_ledger_sha256,"release_record_sha256s":list(self.release_record_sha256s),"released_operation_ids":list(self.released_operation_ids),"released_backup_bytes":self.released_backup_bytes,"remaining_operation_ids":list(self.remaining_operation_ids),"remaining_backup_bytes":self.remaining_backup_bytes,"compacted_ledger_sha256":self.compacted_ledger_sha256}
 def to_bytes(self):return _canonical(self.to_dict())
 @property
 def sha256(self):return _sha(self.to_bytes())
 @classmethod
 def from_bytes(cls,data):
  try:doc=json.loads(data.decode())
  except Exception as exc:raise CheckpointProofError("invalid quota ledger compaction record")from exc
  expected={"schema_version","authority","runtime_authority","promotion","effect","source_ledger_sha256","release_record_sha256s","released_operation_ids","released_backup_bytes","remaining_operation_ids","remaining_backup_bytes","compacted_ledger_sha256"}
  if not isinstance(doc,dict)or set(doc)!=expected or doc["schema_version"]!=1 or doc["authority"]!="synthetic-compaction-quota-ledger-compaction-only" or doc["runtime_authority"]!="none" or doc["promotion"]!="none" or doc["effect"]!="ledger-compacted-provenance-retained":raise CheckpointProofError("quota compaction record boundary is invalid")
  return cls(doc["source_ledger_sha256"],tuple(doc["release_record_sha256s"]),tuple(doc["released_operation_ids"]),doc["released_backup_bytes"],tuple(doc["remaining_operation_ids"]),doc["remaining_backup_bytes"],doc["compacted_ledger_sha256"])
def build_compaction_quota_release_record(ledger,operation_id,*,release_index,reason,previous_release=None):
 match=next((x for x in ledger.reservations if x.operation_id==operation_id),None)
 if match is None:raise CheckpointProofError("quota release operation is absent")
 expected=1 if previous_release is None else previous_release.release_index+1
 if release_index!=expected:raise CheckpointProofError("quota release index is not contiguous")
 if previous_release and previous_release.source_ledger_sha256!=ledger.sha256:raise CheckpointProofError("quota releases reference different source ledgers")
 return CompactionQuotaReleaseRecord(release_index,ledger.sha256,match.operation_id,match.operation_index,match.operation_backup_bytes,match.operation_sha256,previous_release.sha256 if previous_release else _ZERO_HASH,reason)
def compact_compaction_quota_ledger(ledger,releases):
 supplied=tuple(sorted(releases,key=lambda x:x.release_index))
 if not supplied:raise CheckpointProofError("quota ledger compaction requires releases")
 previous=_ZERO_HASH;released=set();by_id={x.operation_id:x for x in ledger.reservations}
 for index,r in enumerate(supplied,1):
  if r.release_index!=index or r.previous_release_sha256!=previous or r.source_ledger_sha256!=ledger.sha256:raise CheckpointProofError("quota release chain is invalid")
  item=by_id.get(r.operation_id)
  if item is None or r.operation_index!=item.operation_index or r.released_backup_bytes!=item.operation_backup_bytes or r.operation_sha256!=item.operation_sha256:raise CheckpointProofError("quota release does not match reservation")
  if r.operation_id in released:raise CheckpointProofError("quota operation released more than once")
  released.add(r.operation_id);previous=r.sha256
 cumulative=0;remaining=[]
 for index,item in enumerate((x for x in ledger.reservations if x.operation_id not in released),1):
  cumulative+=item.operation_backup_bytes;remaining.append(CompactionQuotaReservation(item.operation_id,index,item.operation_backup_bytes,cumulative,item.operation_sha256))
 compacted=CompactionQuotaLedger(ledger.limits,tuple(remaining))
 record=CompactionQuotaLedgerCompactionRecord(ledger.sha256,tuple(x.sha256 for x in supplied),tuple(sorted(released)),sum(by_id[x].operation_backup_bytes for x in released),tuple(sorted(x.operation_id for x in remaining)),cumulative,compacted.sha256)
 return compacted,record
def verify_compaction_quota_ledger_compaction(source,releases,compacted,record):
 expected_ledger,expected_record=compact_compaction_quota_ledger(source,releases)
 if expected_ledger!=compacted or expected_record!=record:raise CheckpointProofError("quota ledger compaction verification failed")
 return True
