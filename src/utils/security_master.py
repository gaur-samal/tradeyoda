"""Security master utilities for option contract mapping."""
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Tuple
from src.utils.logger import log
from src.utils.desktop_config import desktop_config

class SecurityMaster:
    """Manage security master data for option contracts."""
    
    def __init__(self, csv_path: str = None):
        """
        Initialize security master.
        
        Args:
            csv_path: Path to api-scrip-master.csv file
        """
        if csv_path is None:
            # Lazy load desktop config to avoid circular imports
            try:
                # Import directly without triggering package __init__
                import importlib.util
                desktop_config_path = Path(__file__).parent / 'desktop_config.py'
                
                spec = importlib.util.spec_from_file_location("desktop_config_module", str(desktop_config_path))
                desktop_config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(desktop_config_module)
                
                desktop_config = desktop_config_module.desktop_config
                if desktop_config.is_desktop_mode:
                    csv_path = desktop_config.scrip_master_file
                else:
                    # Default path for web/dev mode
                    csv_path = Path(__file__).parent.parent.parent / "api-scrip-master.csv"
            except Exception:
                # Fallback if desktop_config not available
                csv_path = Path(__file__).parent.parent.parent / "api-scrip-master.csv"
        self.csv_path = Path(csv_path)
        self.df = None
        self.load_csv()
    
    def load_csv(self):
        """Load security master CSV file."""
        try:
            if not self.csv_path.exists():
                log.error(f"❌ Security master file not found: {self.csv_path}")
                return False
            
            log.info(f"📂 Loading security master from {self.csv_path}")
            self.df = pd.read_csv(self.csv_path)
            log.info(f"✅ Loaded {len(self.df)} securities")
            
            # Log column names for debugging
            log.info(f"Columns: {list(self.df.columns)}")
            
            return True
        except Exception as e:
            log.error(f"❌ Failed to load security master: {e}")
            return False
    
    def get_option_security_id(
        self,
        symbol: str,
        strike: int,
        option_type: str,
        expiry: str
    ) -> Optional[int]:
        """
        Get security ID for an option contract.

        Args:
            symbol: "NIFTY" or "BANKNIFTY"
            strike: Strike price (e.g., 30150)
            option_type: "CALL" or "PUT" (or "CE"/"PE")
            expiry: Expiry date in YYYY-MM-DD format (e.g., "2025-10-28")

        Returns:
            Security ID as integer, or None if not found
        """
        if self.df is None:
            log.error("❌ Security master not loaded")
            return None

        try:
            # Convert option type
            if option_type in ["CE", "CALL"]:
                option_type_str = "CALL"
            elif option_type in ["PE", "PUT"]:
                option_type_str = "PUT"
            else:
                log.error(f"❌ Invalid option type: {option_type}")
                return None

            # Format expiry date
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
            expiry_formatted = expiry_date.strftime("%d %b").upper()  # "28 OCT"

            # ===== FIX: Ensure strike is integer (no decimal) =====
            strike_int = int(float(strike))  # Converts 26200.0 → 26200

            # Build search string: "NIFTY 28 OCT 30150 CALL"
            search_string = f"{symbol} {expiry_formatted} {strike_int} {option_type_str}"

            log.info(f"🔍 Searching for: {search_string}")

            # Search in SEM_CUSTOM_SYMBOL column
            if 'SEM_CUSTOM_SYMBOL' not in self.df.columns:
                log.error("❌ Column 'SEM_CUSTOM_SYMBOL' not found in CSV")
                log.error(f"Available columns: {list(self.df.columns)}")
                return None

            # Case-insensitive search
            mask = self.df['SEM_CUSTOM_SYMBOL'].str.upper() == search_string.upper()
            matches = self.df[mask]

            if len(matches) == 0:
                log.warning(f"⚠️ No match found for: {search_string}")

                # ===== DEBUG: Show similar options =====
                log.info(f"   Debugging strike format issue...")
                log.info(f"   Input strike: {strike} (type: {type(strike)})")
                log.info(f"   Converted to: {strike_int} (type: {type(strike_int)})")

                # Try to find similar entries
                symbol_mask = self.df['SEM_CUSTOM_SYMBOL'].str.contains(symbol, case=False, na=False)
                expiry_mask = self.df['SEM_CUSTOM_SYMBOL'].str.contains(expiry_formatted, case=False, na=False)
                similar = self.df[symbol_mask & expiry_mask]['SEM_CUSTOM_SYMBOL'].head(10).tolist()

                if similar:
                    log.info(f"   Similar options in CSV for {symbol} {expiry_formatted}:")
                    for opt in similar[:5]:
                        log.info(f"      - {opt}")

                return None

            if len(matches) > 1:
                log.warning(f"⚠️ Multiple matches found for: {search_string}, using first")

            # Get security ID
            security_id = matches.iloc[0]['SEM_SMST_SECURITY_ID']

            log.info(f"✅ Found security ID: {security_id} for {search_string}")

            return int(security_id)

        except Exception as e:
            log.error(f"❌ Error finding security ID: {e}")
            import traceback
            log.error(traceback.format_exc())
            return None

     
    def search_options(self, symbol: str, expiry: str = None, limit: int = 10):
        """
        Search for options matching criteria.
        
        Args:
            symbol: "NIFTY" or "BANKNIFTY"
            expiry: Optional expiry date filter
            limit: Max results to return
        
        Returns:
            DataFrame of matching options
        """
        if self.df is None:
            return pd.DataFrame()
        
        try:
            mask = self.df['SEM_CUSTOM_SYMBOL'].str.contains(symbol, case=False, na=False)
            
            if expiry:
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
                expiry_formatted = expiry_date.strftime("%d %b").upper()
                mask &= self.df['SEM_CUSTOM_SYMBOL'].str.contains(expiry_formatted, case=False, na=False)
            
            results = self.df[mask].head(limit)
            return results[['SEM_CUSTOM_SYMBOL', 'SEM_SMST_SECURITY_ID']]
            
        except Exception as e:
            log.error(f"Error searching options: {e}")
            return pd.DataFrame()


    def get_current_futures_contract(
        self,
        symbol: str
    ) -> Optional[Dict]:
        """
        Get current month futures contract for the symbol.
        Automatically selects the nearest non-expired contract.

        Args:
            symbol: "NIFTY" or "BANKNIFTY"

        Returns:
            Dict with security_id, expiry_date, contract_name, or None
        """
        if self.df is None:
            log.error("❌ Security master not loaded")
            return None

        try:
            now = datetime.now()

            # Search for futures contracts
            # Pattern: "NIFTY NOV FUT", "BANKNIFTY DEC FUT", etc.
            mask = (
                self.df['SEM_CUSTOM_SYMBOL'].str.contains(symbol, case=False, na=False) &
                self.df['SEM_CUSTOM_SYMBOL'].str.contains('FUT', case=False, na=False)
            )

            futures_contracts = self.df[mask].copy()

            if futures_contracts.empty:
                log.error(f"❌ No futures contracts found for {symbol}")
                return None

            log.info(f"📊 Found {len(futures_contracts)} {symbol} futures contracts")

            # Parse expiry dates and filter non-expired
            valid_contracts = []

            for idx, row in futures_contracts.iterrows():
                expiry_str = row.get('SEM_EXPIRY_DATE', '')

                if not expiry_str or pd.isna(expiry_str):
                    continue

                try:
                    # Parse expiry date: '25/11/25 14:30' -> datetime
                    expiry_date = datetime.strptime(str(expiry_str), '%d/%m/%y %H:%M')

                    # Only consider non-expired contracts
                    if expiry_date > now:
                        valid_contracts.append({
                            'security_id': int(row['SEM_SMST_SECURITY_ID']),
                            'contract_name': row['SEM_CUSTOM_SYMBOL'],
                            'expiry_date': expiry_date,
                            'expiry_str': expiry_str
                        })
                except Exception as e:
                    log.debug(f"Could not parse expiry for {row.get('SEM_CUSTOM_SYMBOL')}: {e}")
                    continue

            if not valid_contracts:
                log.error(f"❌ No valid (non-expired) futures contracts found for {symbol}")
                return None

            # Sort by expiry date (nearest first)
            valid_contracts.sort(key=lambda x: x['expiry_date'])

            # Return nearest expiry contract (current month)
            current_contract = valid_contracts[0]

            log.info(f"✅ Current {symbol} futures contract:")
            log.info(f"   Name: {current_contract['contract_name']}")
            log.info(f"   Security ID: {current_contract['security_id']}")
            log.info(f"   Expiry: {current_contract['expiry_date'].strftime('%d-%b-%Y %H:%M')}")

            return current_contract

        except Exception as e:
            log.error(f"❌ Error finding futures contract: {e}")
            import traceback
            log.error(traceback.format_exc())
            return None

    def is_futures_expired(self, expiry_date: datetime) -> bool:
        """
        Check if futures contract has expired.

        Args:
            expiry_date: Expiry datetime

        Returns:
            True if expired
        """
        return datetime.now() > expiry_date

    def get_next_futures_contract(self, symbol: str, current_expiry: datetime) -> Optional[Dict]:
        """
        Get next month's futures contract.

        Args:
            symbol: "NIFTY" or "BANKNIFTY"
            current_expiry: Current contract's expiry date

        Returns:
            Dict with next contract details
        """
        if self.df is None:
            return None

        try:
            # Search for futures contracts after current expiry
            mask = (
                self.df['SEM_CUSTOM_SYMBOL'].str.contains(symbol, case=False, na=False) &
                self.df['SEM_CUSTOM_SYMBOL'].str.contains('FUT', case=False, na=False)
            )

            futures_contracts = self.df[mask].copy()

            next_contracts = []

            for idx, row in futures_contracts.iterrows():
                expiry_str = row.get('SEM_EXPIRY_DATE', '')

                if not expiry_str or pd.isna(expiry_str):
                    continue

                try:
                    expiry_date = datetime.strptime(str(expiry_str), '%d/%m/%y %H:%M')

                    # Only contracts that expire after current
                    if expiry_date > current_expiry:
                        next_contracts.append({
                            'security_id': int(row['SEM_SMST_SECURITY_ID']),
                            'contract_name': row['SEM_CUSTOM_SYMBOL'],
                            'expiry_date': expiry_date,
                            'expiry_str': expiry_str
                        })
                except Exception as e:
                    continue

            if not next_contracts:
                log.warning(f"⚠️ No next futures contract found for {symbol}")
                return None

            # Sort and return nearest
            next_contracts.sort(key=lambda x: x['expiry_date'])
            next_contract = next_contracts[0]

            log.info(f"📅 Next {symbol} futures contract:")
            log.info(f"   Name: {next_contract['contract_name']}")
            log.info(f"   Expiry: {next_contract['expiry_date'].strftime('%d-%b-%Y')}")

            return next_contract

        except Exception as e:
            log.error(f"Error finding next futures contract: {e}")
            return None


# Global instance
security_master = SecurityMaster()


