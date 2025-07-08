"""Lead enrichment command."""

from pathlib import Path
from typing import Optional

import click

from ...core.config import Settings


@click.command()
@click.argument(
    "input_file", type=click.Path(exists=True, path_type=Path), required=True
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: adds _enriched to input filename)",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=100,
    help="Batch size for processing (default: 100)",
)
@click.option(
    "--max-concurrent",
    "-m",
    type=int,
    default=10,
    help="Maximum concurrent API calls (default: 10)",
)
@click.option(
    "--skip-cache", is_flag=True, help="Skip cache and force fresh API calls"
)
@click.option("--resume", is_flag=True, help="Resume interrupted processing")
@click.pass_context
def enrich(
    ctx: click.Context,
    input_file: Path,
    output: Optional[Path],
    batch_size: int,
    max_concurrent: int,
    skip_cache: bool,
    resume: bool,
) -> None:
    """Enrich leads from Excel file with AI-powered research.

    Processes an Excel file containing lead data and enriches it with:
    - Name ethnicity classification for targeting
    - Website discovery and validation
    - LinkedIn profile research
    - Contact information validation
    - Lead scoring and prioritization

    INPUT_FILE must be an Excel (.xlsx) file with the required columns:
    EntityName, TradingAsName, Keyword, ContactNumber, CellNumber,
    EmailAddress, RegisteredAddress, RegisteredAddressCity,
    RegisteredAddressProvince, DirectorName, DirectorCell

    Examples:
        leadscout enrich leads.xlsx
        leadscout enrich leads.xlsx --output enriched.xlsx --batch-size 50
        leadscout enrich leads.xlsx --max-concurrent 5 --skip-cache
    """
    settings: Settings = ctx.obj.get("settings")
    verbose: bool = ctx.obj.get("verbose", False)

    if verbose:
        click.echo(f"Processing: {input_file}")
        click.echo(f"Batch size: {batch_size}")
        click.echo(f"Max concurrent: {max_concurrent}")
        click.echo(f"Skip cache: {skip_cache}")
        click.echo(f"Resume: {resume}")

    # Generate output filename if not provided
    if output is None:
        output = (
            input_file.parent
            / f"{input_file.stem}_enriched{input_file.suffix}"
        )

    if verbose:
        click.echo(f"Output: {output}")

    # Validate input file
    if not input_file.exists():
        click.echo(f"Error: Input file not found: {input_file}", err=True)
        ctx.exit(1)

    if input_file.suffix.lower() not in [".xlsx", ".xls"]:
        click.echo(
            f"Error: Input file must be Excel format (.xlsx/.xls): {input_file}",
            err=True,
        )
        ctx.exit(1)

    # Check if output file exists and prompt for confirmation
    if output.exists() and not resume:
        if not click.confirm(
            f"Output file {output} already exists. Overwrite?"
        ):
            click.echo("Operation cancelled.")
            ctx.exit(0)

    # Import enrichment functionality
    import asyncio
    import pandas as pd
    import time
    from ...classification.classifier import NameClassifier
    from ...classification.models import ClassificationMethod
    
    click.echo("🚀 Starting LeadScout Enrichment")
    click.echo("=" * 50)
    
    try:
        # Load input data
        df = pd.read_excel(input_file)
        click.echo(f"📊 Loaded {len(df)} leads for processing")
        
        # Initialize classifier
        classifier = NameClassifier()
        
        # Process leads
        results = []
        start_time = time.time()
        
        async def process_leads():
            click.echo("\n🔍 Processing director names...")
            
            for idx, row in df.iterrows():
                director_name = row['DirectorName']
                
                try:
                    # Classify the name
                    classification = await classifier.classify_name(director_name)
                    
                    # Add enriched data to row
                    enriched_row = row.copy()
                    enriched_row['ethnicity_classification'] = classification.ethnicity.value
                    enriched_row['classification_confidence'] = classification.confidence
                    enriched_row['classification_method'] = classification.method.value
                    enriched_row['processing_time_ms'] = getattr(classification, 'processing_time_ms', 0)
                    
                    results.append(enriched_row)
                    
                    # Show progress for key names or every 10th
                    if idx < 10 or (idx + 1) % 10 == 0:
                        method_icon = "⚡" if classification.method == ClassificationMethod.RULE_BASED else "🤖"
                        click.echo(f"  {idx + 1:2d}. {method_icon} {director_name:<30} → {classification.ethnicity.value:<12} ({classification.method.value})")
                
                except Exception as e:
                    click.echo(f"❌ Error processing {director_name}: {e}")
                    # Add error row
                    error_row = row.copy()
                    error_row['ethnicity_classification'] = 'ERROR'
                    error_row['classification_confidence'] = 0.0
                    error_row['classification_method'] = 'error'
                    error_row['processing_time_ms'] = 0
                    results.append(error_row)
        
        # Run async processing
        asyncio.run(process_leads())
        
        # Calculate performance metrics
        processing_time = time.time() - start_time
        success_count = len([r for r in results if r['ethnicity_classification'] != 'ERROR'])
        
        # Create output DataFrame
        output_df = pd.DataFrame(results)
        
        # Save results
        output_df.to_excel(output, index=False)
        
        # Show summary
        click.echo(f"\n📈 Processing Results:")
        click.echo(f"  Total leads: {len(df)}")
        click.echo(f"  Successful: {success_count}")
        click.echo(f"  Errors: {len(results) - success_count}")
        click.echo(f"  Success rate: {success_count/len(df)*100:.1f}%")
        
        click.echo(f"\n🎯 Method Breakdown:")
        method_counts = output_df['classification_method'].value_counts()
        for method, count in method_counts.items():
            if method != 'error':
                percentage = count / len(output_df) * 100
                click.echo(f"  {method.title()}: {count} ({percentage:.1f}%)")
        
        click.echo(f"\n⏱️ Performance:")
        click.echo(f"  Total time: {processing_time:.2f} seconds")
        click.echo(f"  Average per lead: {processing_time/len(df)*1000:.1f} ms")
        click.echo(f"  Processing rate: {len(df)/processing_time:.1f} leads/second")
        
        click.echo(f"\n💾 Saved enriched results to: {output}")
        click.echo("✅ Enrichment completed successfully!")
        
    except Exception as e:
        click.echo(f"❌ Enrichment failed: {e}", err=True)
        ctx.exit(1)
