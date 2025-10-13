import argparse, shutil, os

def clear_tenant_memory(tenant_id: str):
    """Clear per-tenant memory including both buffer and summary files"""
    root = os.path.join(".state", "memory", tenant_id)
    if os.path.exists(root):
        shutil.rmtree(root)
        print(f"Cleared memory for {tenant_id}")
        return True
    else:
        print(f"No memory state found for {tenant_id}")
        return False

def main():
    ap = argparse.ArgumentParser(description="Clear per-tenant memory")
    ap.add_argument("--tenant", required=True, choices=["U1", "U2", "U3", "U4"], help="Tenant ID")
    args = ap.parse_args()
    clear_tenant_memory(args.tenant)

if __name__ == "__main__":
    main()
